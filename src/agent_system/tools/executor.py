from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    returncode: int
    script_path: Path

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


class PythonExecutor:
    def __init__(self, timeout_seconds: int = 8, python_command: str = "py") -> None:
        self.timeout_seconds = timeout_seconds
        self.python_command = python_command

    def run(self, code: str) -> ExecutionResult:
        with tempfile.TemporaryDirectory(prefix="agent_system_") as temp_dir:
            script_path = Path(temp_dir) / "generated_task.py"
            script_path.write_text(code, encoding="utf-8")
            try:
                completed = subprocess.run(
                    [self.python_command, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
                return ExecutionResult(
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    returncode=completed.returncode,
                    script_path=script_path,
                )
            except subprocess.TimeoutExpired as exc:
                return ExecutionResult(
                    stdout=exc.stdout or "",
                    stderr=f"Execution timed out after {self.timeout_seconds}s.",
                    returncode=124,
                    script_path=script_path,
                )
