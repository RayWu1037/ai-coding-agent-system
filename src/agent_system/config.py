from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    backend: str
    fast_mode: bool
    student_mode: bool
    budget_mode: bool
    openai_api_key: str | None
    anthropic_api_key: str | None
    gemini_api_key: str | None
    openai_model: str
    anthropic_model: str
    gemini_model: str
    codex_model: str | None
    claude_cli_path: str | None
    codex_cli_path: str | None
    demo_mode: bool
    cli_timeout_seconds: int
    execution_timeout_seconds: int
    max_debug_iterations: int
    provider_cooldown_seconds: int
    provider_max_retries: int

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)


def load_settings() -> Settings:
    _load_dotenv()
    return Settings(
        backend=os.getenv("AGENT_BACKEND", "auto"),
        fast_mode=_parse_bool(os.getenv("AGENT_FAST_MODE", "0")),
        student_mode=_parse_bool(os.getenv("AGENT_STUDENT_MODE", "0")),
        budget_mode=_parse_bool(os.getenv("AGENT_BUDGET_MODE", "0")),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "sonnet"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        codex_model=os.getenv("CODEX_MODEL"),
        claude_cli_path=os.getenv("CLAUDE_CLI_PATH"),
        codex_cli_path=os.getenv("CODEX_CLI_PATH"),
        demo_mode=_parse_bool(os.getenv("AGENT_DEMO_MODE", "0")),
        cli_timeout_seconds=int(os.getenv("CLI_TIMEOUT_SECONDS", "300")),
        execution_timeout_seconds=int(os.getenv("EXECUTION_TIMEOUT_SECONDS", "8")),
        max_debug_iterations=int(os.getenv("MAX_DEBUG_ITERATIONS", "3")),
        provider_cooldown_seconds=int(os.getenv("PROVIDER_COOLDOWN_SECONDS", "900")),
        provider_max_retries=int(os.getenv("PROVIDER_MAX_RETRIES", "1")),
    )


def _load_dotenv() -> None:
    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
