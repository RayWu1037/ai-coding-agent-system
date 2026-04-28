from __future__ import annotations

import subprocess
import sys
import uuid
import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

from agent_system.config import Settings, load_settings
from agent_system.llm import _resolve_executable
from agent_system.tools.executor import PythonExecutor


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def run_doctor(live: bool = False, output_path: Path | None = None) -> int:
    settings = load_settings()
    results = collect_doctor_results(settings=settings, live=live)
    report = format_doctor_report(settings, results, live=live)
    print(report)
    if output_path is not None:
        write_doctor_report(output_path, settings=settings, results=results, live=live)
        print(f"\nSaved doctor report to {output_path}")
    return 1 if any(result.status == "fail" for result in results) else 0


def collect_doctor_results(settings: Settings, live: bool = False) -> list[CheckResult]:
    results: list[CheckResult] = []

    claude_path = _resolve_executable(
        settings.claude_cli_path,
        [
            "claude",
            str(Path.home() / ".local" / "bin" / "claude.exe"),
        ],
    )
    codex_path = _resolve_executable(
        settings.codex_cli_path,
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

    results.append(_check_python_runtime())
    results.append(_check_scratch_writable())
    results.append(_check_executor(settings))
    results.append(_check_cli_path("Claude CLI", claude_path))
    results.append(_check_cli_path("Codex CLI", codex_path))
    results.append(_check_api_key("Anthropic API key", settings.has_anthropic))
    results.append(_check_api_key("OpenAI API key", settings.has_openai))
    results.append(_check_backend_readiness(settings, claude_path, codex_path))

    if live:
        results.append(_probe_claude_cli(claude_path, settings))
        results.append(_probe_codex_cli(codex_path, settings))
    else:
        results.append(
            CheckResult(
                "Live provider probes",
                "skip",
                "Skipped. Re-run with --doctor-live to test authenticated CLI calls.",
            )
        )

    return results


def format_doctor_report(settings: Settings, results: list[CheckResult], live: bool) -> str:
    lines = [
        "=== DOCTOR ===",
        f"backend={settings.backend} fast_mode={settings.fast_mode} live_probes={live}",
        "",
    ]
    for result in results:
        lines.append(f"[{result.status.upper():4}] {result.name}: {result.detail}")
    return "\n".join(lines)


def doctor_report_payload(
    settings: Settings,
    results: list[CheckResult],
    live: bool,
) -> dict[str, object]:
    return {
        "backend": settings.backend,
        "fast_mode": settings.fast_mode,
        "live_probes": live,
        "results": [asdict(result) for result in results],
    }


def write_doctor_report(
    output_path: Path,
    settings: Settings,
    results: list[CheckResult],
    live: bool,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".json":
        payload = doctor_report_payload(settings, results, live=live)
        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return
    output_path.write_text(format_doctor_markdown(settings, results, live=live), encoding="utf-8")


def format_doctor_markdown(settings: Settings, results: list[CheckResult], live: bool) -> str:
    lines = [
        "# Doctor Report",
        "",
        f"- Backend: `{settings.backend}`",
        f"- Fast mode: `{settings.fast_mode}`",
        f"- Live probes: `{live}`",
        "",
        "| Status | Check | Detail |",
        "| --- | --- | --- |",
    ]
    for result in results:
        detail = result.detail.replace("\n", "<br>")
        lines.append(f"| `{result.status}` | {result.name} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def _check_python_runtime() -> CheckResult:
    return CheckResult(
        "Python runtime",
        "ok",
        f"{sys.executable} ({sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})",
    )


def _check_scratch_writable() -> CheckResult:
    scratch_root = Path.cwd() / ".agent_system_runs"
    try:
        scratch_root.mkdir(parents=True, exist_ok=True)
        probe = scratch_root / f"doctor-write-test-{uuid.uuid4().hex}.txt"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return CheckResult("Scratch directory", "ok", f"Writable: {scratch_root}")
    except OSError as exc:
        return CheckResult("Scratch directory", "fail", f"Not writable: {scratch_root} ({exc})")


def _check_executor(settings: Settings) -> CheckResult:
    executor = PythonExecutor(
        timeout_seconds=max(3, min(settings.execution_timeout_seconds, 8)),
        python_command=sys.executable,
        workspace_root=Path.cwd(),
    )
    code = "from pathlib import Path\nprint(Path.cwd().name)\n"
    result = executor.run(code)
    if result.succeeded and result.stdout.strip() == result.script_path.parent.name:
        return CheckResult("Python executor", "ok", "Runs code in an isolated working directory.")
    detail = result.stderr.strip() or result.stdout.strip() or "Executor self-check failed."
    return CheckResult("Python executor", "fail", detail)


def _check_cli_path(name: str, path: str | None) -> CheckResult:
    if path is None:
        return CheckResult(name, "warn", "Executable not found on PATH or configured location.")
    return CheckResult(name, "ok", f"Resolved executable: {path}")


def _check_api_key(name: str, present: bool) -> CheckResult:
    if present:
        return CheckResult(name, "ok", "Configured.")
    return CheckResult(name, "warn", "Not configured.")


def _check_backend_readiness(
    settings: Settings,
    claude_path: str | None,
    codex_path: str | None,
) -> CheckResult:
    has_cli_pair = bool(claude_path and codex_path)
    has_sdk_pair = bool(settings.has_anthropic and settings.has_openai)
    if settings.backend == "cli":
        if has_cli_pair:
            return CheckResult("Backend readiness", "ok", "CLI backend has both Claude and Codex available.")
        return CheckResult("Backend readiness", "fail", "CLI backend requires both Claude CLI and Codex CLI.")
    if settings.backend == "sdk":
        if has_sdk_pair:
            return CheckResult("Backend readiness", "ok", "SDK backend has both Anthropic and OpenAI keys.")
        return CheckResult("Backend readiness", "fail", "SDK backend requires both Anthropic and OpenAI keys.")
    if has_cli_pair or has_sdk_pair:
        mode = "CLI pair" if has_cli_pair else "SDK pair"
        return CheckResult("Backend readiness", "ok", f"Auto backend can run with the available {mode}.")
    return CheckResult("Backend readiness", "fail", "Auto backend has neither a full CLI pair nor a full SDK pair.")


def _probe_claude_cli(path: str | None, settings: Settings) -> CheckResult:
    if path is None:
        return CheckResult("Claude live probe", "skip", "Claude CLI not available.")
    command = [
        path,
        "-p",
        "--output-format",
        "text",
        "--permission-mode",
        "default",
    ]
    if settings.anthropic_model:
        command.extend(["--model", settings.anthropic_model])
    command.append("Reply with OK only.")
    return _run_provider_probe("Claude live probe", command, expect="OK")


def _probe_codex_cli(path: str | None, settings: Settings) -> CheckResult:
    if path is None:
        return CheckResult("Codex live probe", "skip", "Codex CLI not available.")
    scratch_root = Path.cwd() / ".agent_system_runs"
    scratch_root.mkdir(parents=True, exist_ok=True)
    output_path = scratch_root / f"doctor-codex-{uuid.uuid4().hex}.txt"
    command = [
        path,
        "exec",
        "-",
        "--skip-git-repo-check",
        "-C",
        str(Path.cwd()),
        "-o",
        str(output_path),
        "--color",
        "never",
    ]
    if settings.codex_model:
        command.extend(["--model", settings.codex_model])
    try:
        completed = subprocess.run(
            command,
            input="Reply with OK only.",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=min(settings.cli_timeout_seconds, 90),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult("Codex live probe", "fail", f"Timed out: {exc}")
    finally:
        probe_text = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else ""
        output_path.unlink(missing_ok=True)

    if completed.returncode == 0:
        normalized = (probe_text or completed.stdout).strip()
        return CheckResult("Codex live probe", "ok", f"Healthy. Sample response: {normalized[:60] or 'OK'}")
    return _classify_probe_failure("Codex live probe", completed.stderr.strip() or completed.stdout.strip())


def _run_provider_probe(name: str, command: list[str], expect: str) -> CheckResult:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult(name, "fail", f"Timed out: {exc}")

    if completed.returncode == 0:
        output = completed.stdout.strip()
        if expect.casefold() in output.casefold():
            return CheckResult(name, "ok", f"Healthy. Sample response: {output[:60]}")
        return CheckResult(name, "warn", f"CLI responded, but not with expected text: {output[:100]}")
    return _classify_probe_failure(name, completed.stderr.strip() or completed.stdout.strip())


def _classify_probe_failure(name: str, detail: str) -> CheckResult:
    lowered = detail.casefold()
    if not detail:
        return CheckResult(name, "fail", "Command failed with no output.")
    if "not logged in" in lowered or "/login" in lowered:
        return CheckResult(name, "fail", detail)
    if "usage limit" in lowered or "quota" in lowered or "credits" in lowered:
        return CheckResult(name, "warn", detail)
    if "access is denied" in lowered or "拒绝访问" in lowered:
        return CheckResult(name, "fail", detail)
    return CheckResult(name, "fail", detail)
