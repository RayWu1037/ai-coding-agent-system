from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from anthropic import Anthropic
from openai import OpenAI

from agent_system.config import Settings


class LLMError(RuntimeError):
    """Raised when no suitable LLM provider is configured."""


class AggregateLLMError(LLMError):
    """Raised when every configured provider fails."""

    def __init__(self, operation: str, errors: list[str]) -> None:
        joined = "\n".join(f"- {error}" for error in errors)
        super().__init__(f"All providers failed for {operation}:\n{joined}")
        self.operation = operation
        self.errors = errors


@dataclass
class Message:
    system: str
    user: str

    def combined_prompt(self) -> str:
        return f"System instructions:\n{self.system}\n\nUser request:\n{self.user}".strip()


class AnthropicClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def complete(self, message: Message, max_tokens: int = 1600) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=message.system,
            messages=[{"role": "user", "content": message.user}],
        )
        chunks: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                chunks.append(text)
        return _normalize_model_text("".join(chunks))


class OpenAIClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, message: Message) -> str:
        response = self._client.responses.create(
            model=self._model,
            input=[
                {"role": "system", "content": message.system},
                {"role": "user", "content": message.user},
            ],
        )
        return _normalize_model_text(response.output_text)


class ClaudeCLIClient:
    def __init__(self, executable: str, model: str, timeout_seconds: int) -> None:
        self._executable = executable
        self._model = model
        self._timeout_seconds = timeout_seconds

    def complete(self, message: Message) -> str:
        command = [
            self._executable,
            "-p",
            "--output-format",
            "text",
            "--permission-mode",
            "default",
            "--system-prompt",
            message.system,
        ]
        if self._model:
            command.extend(["--model", self._model])
        command.append(message.user)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self._timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"Claude CLI timed out after {self._timeout_seconds}s."
            ) from exc
        if completed.returncode != 0:
            raise LLMError(completed.stderr.strip() or "Claude CLI call failed.")
        return _normalize_model_text(completed.stdout)


class CodexCLIClient:
    def __init__(
        self,
        executable: str,
        model: str | None,
        timeout_seconds: int,
        workspace: Path,
    ) -> None:
        self._executable = executable
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._workspace = workspace

    def complete(self, message: Message) -> str:
        scratch_dir = self._workspace / ".agent_system_runs"
        scratch_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix="codex-last-message-",
            suffix=".txt",
            delete=False,
            dir=scratch_dir,
        ) as handle:
            output_path = Path(handle.name)

        try:
            command = [
                self._executable,
                "exec",
                "-",
                "--skip-git-repo-check",
                "-C",
                str(self._workspace),
                "-o",
                str(output_path),
                "--color",
                "never",
            ]
            if self._model:
                command.extend(["--model", self._model])
            try:
                completed = subprocess.run(
                    command,
                    input=message.combined_prompt(),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=self._timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise TimeoutError(
                    f"Codex CLI timed out after {self._timeout_seconds}s."
                ) from exc
            if completed.returncode != 0:
                raise LLMError(completed.stderr.strip() or "Codex CLI call failed.")
            if output_path.exists():
                return _normalize_model_text(output_path.read_text(encoding="utf-8"))
            return _normalize_model_text(completed.stdout)
        finally:
            output_path.unlink(missing_ok=True)


class LLMRegistry:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._claude_cli = None
        self._codex_cli = None
        self._anthropic = (
            AnthropicClient(settings.anthropic_api_key, settings.anthropic_model)
            if settings.has_anthropic
            else None
        )
        self._openai = (
            OpenAIClient(settings.openai_api_key, settings.openai_model)
            if settings.has_openai
            else None
        )
        self._initialize_cli_clients()

    def plan_and_code(self, message: Message) -> str:
        candidates: list[tuple[str, Callable[[], str]]] = []
        if self._claude_cli is not None:
            candidates.append(("Claude CLI", lambda: self._claude_cli.complete(message)))
        if self._codex_cli is not None:
            candidates.append(("Codex CLI", lambda: self._codex_cli.complete(message)))
        if self._anthropic is not None:
            candidates.append(("Anthropic API", lambda: self._anthropic.complete(message)))
        if self._openai is not None:
            candidates.append(("OpenAI API", lambda: self._openai.complete(message)))
        if self._settings.backend == "cli" and not candidates:
            raise LLMError("CLI backend requested but no planning/coding provider is available.")
        return self._complete_with_fallback("planning/coding", candidates)

    def debug_and_review(self, message: Message) -> str:
        candidates: list[tuple[str, Callable[[], str]]] = []
        if self._codex_cli is not None:
            candidates.append(("Codex CLI", lambda: self._codex_cli.complete(message)))
        if self._claude_cli is not None:
            candidates.append(("Claude CLI", lambda: self._claude_cli.complete(message)))
        if self._openai is not None:
            candidates.append(("OpenAI API", lambda: self._openai.complete(message)))
        if self._anthropic is not None:
            candidates.append(("Anthropic API", lambda: self._anthropic.complete(message)))
        if self._settings.backend == "cli" and not candidates:
            raise LLMError("CLI backend requested but no debugging/review provider is available.")
        return self._complete_with_fallback("debugging/review", candidates)

    def _complete_with_fallback(
        self,
        operation: str,
        candidates: list[tuple[str, Callable[[], str]]],
    ) -> str:
        if not candidates:
            raise LLMError(f"No provider configured for {operation}.")

        errors: list[str] = []
        for label, complete in candidates:
            try:
                return complete()
            except TimeoutError as exc:
                errors.append(f"{label}: {exc}")
            except LLMError as exc:
                errors.append(f"{label}: {exc}")
        raise AggregateLLMError(operation, errors)

    def _initialize_cli_clients(self) -> None:
        if self._settings.backend not in {"auto", "cli"}:
            return

        claude_path = _resolve_executable(
            self._settings.claude_cli_path,
            [
                "claude",
                str(Path.home() / ".local" / "bin" / "claude.exe"),
            ],
        )
        codex_path = _resolve_executable(
            self._settings.codex_cli_path,
            [
                str(
                    Path.home()
                    / "AppData"
                    / "Roaming"
                    / "npm"
                    / "node_modules"
                    / "@openai"
                    / "codex"
                    / "node_modules"
                    / "@openai"
                    / "codex-win32-x64"
                    / "vendor"
                    / "x86_64-pc-windows-msvc"
                    / "codex"
                    / "codex.exe"
                ),
                str(Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd"),
                "codex.cmd",
                "codex",
            ],
        )
        workspace = Path.cwd()

        if claude_path is not None:
            self._claude_cli = ClaudeCLIClient(
                executable=claude_path,
                model=self._settings.anthropic_model,
                timeout_seconds=self._settings.cli_timeout_seconds,
            )
        if codex_path is not None:
            self._codex_cli = CodexCLIClient(
                executable=codex_path,
                model=self._settings.codex_model,
                timeout_seconds=self._settings.cli_timeout_seconds,
                workspace=workspace,
            )


def _normalize_model_text(text: str | None) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def _resolve_executable(configured: str | None, candidates: list[str]) -> str | None:
    if configured:
        path = Path(configured)
        if path.exists():
            return str(path)
        resolved = shutil.which(configured)
        if resolved:
            return resolved
        return None

    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return str(path)
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None
