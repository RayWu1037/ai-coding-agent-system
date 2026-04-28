from __future__ import annotations

import json
import re
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_system.controller import RunSummary


@dataclass
class SessionState:
    id: str
    task: str
    backend: str
    fast_mode: bool
    created_at: str
    status: str = "starting"
    message: str = ""
    iterations: int | None = None
    timeline: list[dict[str, str]] = field(default_factory=list)
    plan: str = ""
    review: str = ""
    success: bool | None = None
    failure_stage: str = ""
    last_stdout: str = ""
    last_stderr: str = ""
    final_code_path: str = ""
    handoff_path: str = ""


class SessionRecorder:
    def __init__(
        self,
        task: str,
        backend: str,
        fast_mode: bool,
        iterations: int | None,
        root_dir: Path | None = None,
    ) -> None:
        self.root_dir = root_dir or (Path.cwd() / ".agent_system_sessions")
        self.root_dir.mkdir(parents=True, exist_ok=True)
        session_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        self.session_dir = self.root_dir / session_id
        self.session_dir.mkdir(parents=True, exist_ok=False)
        self.state = SessionState(
            id=session_id,
            task=task,
            backend=backend,
            fast_mode=fast_mode,
            created_at=datetime.now(timezone.utc).isoformat(),
            iterations=iterations,
        )
        self._write_state()

    def update(self, stage: str, message: str) -> None:
        self.state.status = stage
        self.state.message = message
        self.state.timeline.append({"stage": stage, "message": message})
        self._write_state()

    def finish(self, summary: RunSummary) -> None:
        code_path = self.session_dir / "final_code.py"
        code_path.write_text(summary.final_code, encoding="utf-8")
        handoff_path = self.session_dir / "handoff.md"
        handoff_path.write_text(
            build_handoff_markdown(self.state.task, summary, code_path),
            encoding="utf-8",
        )
        self.state.plan = summary.plan
        self.state.review = summary.review
        self.state.success = summary.success
        self.state.failure_stage = summary.failure_stage
        self.state.last_stdout = summary.last_stdout
        self.state.last_stderr = summary.last_stderr
        self.state.final_code_path = str(code_path)
        self.state.handoff_path = str(handoff_path)
        self.state.status = "done"
        self.state.message = "Completed."
        self._write_state()

    def fail(self, error: str) -> None:
        self.state.status = "failed"
        self.state.message = error
        self.state.timeline.append({"stage": "failed", "message": error})
        self._write_state()

    def save_report_aliases(self) -> None:
        latest_dir = self.root_dir / "latest"
        if latest_dir.exists():
            shutil.rmtree(latest_dir, ignore_errors=True)
        shutil.copytree(self.session_dir, latest_dir)

    def _write_state(self) -> None:
        state_path = self.session_dir / "session.json"
        state_path.write_text(json.dumps(asdict(self.state), indent=2, ensure_ascii=False), encoding="utf-8")


def build_handoff_markdown(task: str, summary: RunSummary, code_path: Path) -> str:
    status_line = "success" if summary.success else "needs work"
    compact_review = _compact_text(summary.review, 900)
    compact_stdout = _compact_text(summary.last_stdout, 500)
    compact_stderr = _compact_text(summary.last_stderr, 700)
    next_step = _suggest_next_step(summary)
    return "\n".join(
        [
            "# Handoff Summary",
            "",
            f"- Task: {task}",
            f"- Status: `{status_line}`",
            f"- Iterations used: `{summary.iterations_used}`",
            f"- Failure stage: `{summary.failure_stage or 'none'}`",
            f"- Final code: `{code_path}`",
            "",
            "## Compact Plan",
            "",
            summary.plan or "_No plan recorded._",
            "",
            "## Review Summary",
            "",
            compact_review or "_No review recorded._",
            "",
            "## Last Stdout",
            "",
            compact_stdout or "_No stdout recorded._",
            "",
            "## Last Stderr",
            "",
            compact_stderr or "_No stderr recorded._",
            "",
            "## Next Prompt",
            "",
            build_next_prompt(task, code_path, summary, next_step),
            "",
        ]
    )


def build_next_prompt(task: str, code_path: Path, summary: RunSummary, next_step: str) -> str:
    return (
        "Continue this coding task from the saved local artifact.\n"
        f"Task: {task}\n"
        f"Load code from: {code_path}\n"
        f"Current status: {'success' if summary.success else 'not yet successful'}\n"
        f"Most recent failure stage: {summary.failure_stage or 'none'}\n"
        f"Next step: {next_step}\n"
        "Keep changes minimal, preserve working parts, and return only the updated code."
    )


def _suggest_next_step(summary: RunSummary) -> str:
    if summary.success and summary.review.strip():
        return "Address the highest-value reviewer finding without breaking the passing behavior."
    if summary.failure_stage == "validation":
        return "Fix semantic output quality so the artifact passes validation."
    if summary.failure_stage:
        return "Fix the latest execution failure and rerun the task."
    return "Inspect the saved code and continue from the last stable point."


def _compact_text(text: str, max_chars: int) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rsplit(" ", 1)[0].rstrip() + "..."
