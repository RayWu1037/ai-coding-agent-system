from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    backend: str
    openai_api_key: str | None
    anthropic_api_key: str | None
    openai_model: str
    anthropic_model: str
    codex_model: str | None
    claude_cli_path: str | None
    codex_cli_path: str | None
    cli_timeout_seconds: int
    execution_timeout_seconds: int
    max_debug_iterations: int

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)


def load_settings() -> Settings:
    _load_dotenv()
    return Settings(
        backend=os.getenv("AGENT_BACKEND", "auto"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "sonnet"),
        codex_model=os.getenv("CODEX_MODEL"),
        claude_cli_path=os.getenv("CLAUDE_CLI_PATH"),
        codex_cli_path=os.getenv("CODEX_CLI_PATH"),
        cli_timeout_seconds=int(os.getenv("CLI_TIMEOUT_SECONDS", "120")),
        execution_timeout_seconds=int(os.getenv("EXECUTION_TIMEOUT_SECONDS", "8")),
        max_debug_iterations=int(os.getenv("MAX_DEBUG_ITERATIONS", "3")),
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
