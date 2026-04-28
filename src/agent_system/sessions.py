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
    current_code_path: str = ""
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
        self.checkpoint(
            plan=summary.plan,
            code=summary.final_code,
            review=summary.review,
            success=summary.success,
            iterations_used=summary.iterations_used,
            failure_stage=summary.failure_stage,
            last_stdout=summary.last_stdout,
            last_stderr=summary.last_stderr,
            final=True,
        )
        self.state.plan = summary.plan
        self.state.review = summary.review
        self.state.success = summary.success
        self.state.failure_stage = summary.failure_stage
        self.state.last_stdout = summary.last_stdout
        self.state.last_stderr = summary.last_stderr
        self.state.status = "done"
        self.state.message = "Completed."
        self._write_state()

    def fail(self, error: str) -> None:
        self.state.status = "failed"
        self.state.message = error
        self.state.timeline.append({"stage": "failed", "message": error})
        if self.state.handoff_path:
            handoff_path = Path(self.state.handoff_path)
            existing_code = self.state.current_code_path or self.state.final_code_path
            code_path = Path(existing_code) if existing_code else self.session_dir / "current_code.py"
            handoff_path.write_text(
                build_next_handoff_markdown(
                    task=self.state.task,
                    plan=self.state.plan,
                    review=self.state.review,
                    success=False,
                    iterations_used=self.state.iterations or 0,
                    failure_stage=self.state.failure_stage or "interrupted",
                    last_stdout=self.state.last_stdout,
                    last_stderr=error if not self.state.last_stderr else self.state.last_stderr,
                    code_path=code_path,
                ),
                encoding="utf-8",
            )
        self._write_state()

    def save_report_aliases(self) -> None:
        latest_dir = self.root_dir / "latest"
        if latest_dir.exists():
            shutil.rmtree(latest_dir, ignore_errors=True)
        shutil.copytree(self.session_dir, latest_dir)

    def _write_state(self) -> None:
        state_path = self.session_dir / "session.json"
        state_path.write_text(json.dumps(asdict(self.state), indent=2, ensure_ascii=False), encoding="utf-8")

    def checkpoint(
        self,
        *,
        plan: str | None = None,
        code: str | None = None,
        review: str | None = None,
        success: bool | None = None,
        iterations_used: int | None = None,
        failure_stage: str = "",
        last_stdout: str = "",
        last_stderr: str = "",
        final: bool = False,
    ) -> None:
        if plan is not None:
            self.state.plan = plan
        if review is not None:
            self.state.review = review
        if success is not None:
            self.state.success = success
        if iterations_used is not None:
            self.state.iterations = iterations_used
        if failure_stage:
            self.state.failure_stage = failure_stage
        if last_stdout:
            self.state.last_stdout = last_stdout
        if last_stderr:
            self.state.last_stderr = last_stderr

        code_path = self.session_dir / ("final_code.py" if final else "current_code.py")
        if code is not None:
            code_path.write_text(code, encoding="utf-8")
            if final:
                self.state.final_code_path = str(code_path)
            else:
                self.state.current_code_path = str(code_path)
        else:
            existing = self.state.final_code_path if final else self.state.current_code_path
            code_path = Path(existing) if existing else code_path

        handoff_path = self.session_dir / "handoff.md"
        handoff_path.write_text(
            build_next_handoff_markdown(
                task=self.state.task,
                plan=self.state.plan,
                review=self.state.review,
                success=self.state.success,
                iterations_used=self.state.iterations or 0,
                failure_stage=self.state.failure_stage,
                last_stdout=self.state.last_stdout,
                last_stderr=self.state.last_stderr,
                code_path=code_path,
            ),
            encoding="utf-8",
        )
        self.state.handoff_path = str(handoff_path)
        self._write_state()


def build_handoff_markdown(task: str, summary: RunSummary, code_path: Path) -> str:
    return build_next_handoff_markdown(
        task=task,
        plan=summary.plan,
        review=summary.review,
        success=summary.success,
        iterations_used=summary.iterations_used,
        failure_stage=summary.failure_stage,
        last_stdout=summary.last_stdout,
        last_stderr=summary.last_stderr,
        code_path=code_path,
    )


def build_next_handoff_markdown(
    *,
    task: str,
    plan: str,
    review: str,
    success: bool | None,
    iterations_used: int,
    failure_stage: str,
    last_stdout: str,
    last_stderr: str,
    code_path: Path,
) -> str:
    status_line = "success" if success else "needs work"
    compact_review = _compact_text(review, 900)
    compact_stdout = _compact_text(last_stdout, 500)
    compact_stderr = _compact_text(last_stderr, 700)
    next_step = _suggest_next_step_from_fields(success, failure_stage, review)
    return "\n".join(
        [
            "# Handoff Summary",
            "",
            f"- Task: {task}",
            f"- Status: `{status_line}`",
            f"- Iterations used: `{iterations_used}`",
            f"- Failure stage: `{failure_stage or 'none'}`",
            f"- Final code: `{code_path}`",
            "",
            "## Compact Plan",
            "",
            plan or "_No plan recorded._",
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
            build_next_prompt(
                task=task,
                code_path=code_path,
                success=success,
                failure_stage=failure_stage,
                next_step=next_step,
            ),
            "",
        ]
    )


def build_next_prompt(
    *,
    task: str,
    code_path: Path,
    success: bool | None,
    failure_stage: str,
    next_step: str,
) -> str:
    return (
        "Continue this coding task from the saved local artifact.\n"
        f"Task: {task}\n"
        f"Load code from: {code_path}\n"
        f"Current status: {'success' if success else 'not yet successful'}\n"
        f"Most recent failure stage: {failure_stage or 'none'}\n"
        f"Next step: {next_step}\n"
        "Keep changes minimal, preserve working parts, and return only the updated code."
    )


def _suggest_next_step(summary: RunSummary) -> str:
    return _suggest_next_step_from_fields(
        summary.success,
        summary.failure_stage,
        summary.review,
    )


def _suggest_next_step_from_fields(
    success: bool | None,
    failure_stage: str,
    review: str,
) -> str:
    if success and review.strip():
        return "Address the highest-value reviewer finding without breaking the passing behavior."
    if failure_stage == "validation":
        return "Fix semantic output quality so the artifact passes validation."
    if failure_stage:
        return "Fix the latest execution failure and rerun the task."
    return "Inspect the saved code and continue from the last stable point."


def _compact_text(text: str, max_chars: int) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rsplit(" ", 1)[0].rstrip() + "..."
