import shutil
import unittest
import uuid
from pathlib import Path

from agent_system.controller import RunSummary
from agent_system.sessions import SessionRecorder, build_handoff_markdown


class SessionTests(unittest.TestCase):
    def test_build_handoff_markdown_contains_next_prompt(self) -> None:
        summary = RunSummary(
            plan="1. Build a small tool.",
            final_code="print('ok')\n",
            review="Fix one validator issue.",
            iterations_used=2,
            success=False,
            last_stdout="",
            last_stderr="Semantic validation failed: bad title",
            failure_stage="validation",
        )

        text = build_handoff_markdown("Build a note ingester", summary, Path("final_code.py"))

        self.assertIn("# Handoff Summary", text)
        self.assertIn("Continue this coding task from the saved local artifact.", text)
        self.assertIn("Fix semantic output quality", text)

    def test_session_recorder_writes_state_and_handoff(self) -> None:
        root = Path.cwd() / ".test_sessions" / uuid.uuid4().hex
        root.mkdir(parents=True, exist_ok=False)
        self.addCleanup(shutil.rmtree, root, True)
        recorder = SessionRecorder(
            task="Build a todo app",
            backend="cli",
            fast_mode=False,
            iterations=2,
            root_dir=root,
        )
        recorder.update("planning", "Making a plan.")
        recorder.finish(
            RunSummary(
                plan="1. Build app.",
                final_code="print('ok')\n",
                review="No issues found.",
                iterations_used=1,
                success=True,
            )
        )

        self.assertTrue((recorder.session_dir / "session.json").exists())
        self.assertTrue((recorder.session_dir / "handoff.md").exists())
        self.assertTrue((recorder.session_dir / "final_code.py").exists())


if __name__ == "__main__":
    unittest.main()
