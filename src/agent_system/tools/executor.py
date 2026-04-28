from __future__ import annotations

import shutil
import subprocess
import uuid
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
    def __init__(
        self,
        timeout_seconds: int = 8,
        python_command: str = "py",
        workspace_root: Path | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.python_command = python_command
        self.workspace_root = workspace_root or Path.cwd()
        self.scratch_root = self.workspace_root / ".agent_system_runs"
        self.scratch_root.mkdir(exist_ok=True)

    def run(self, code: str) -> ExecutionResult:
        run_dir = self.scratch_root / uuid.uuid4().hex
        run_dir.mkdir(parents=True, exist_ok=False)
        script_path = run_dir / "generated_task.py"
        try:
            script_path.write_text(code, encoding="utf-8")
            try:
                completed = subprocess.run(
                    [self.python_command, str(script_path)],
                    capture_output=True,
                    text=True,
                    cwd=run_dir,
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
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)
