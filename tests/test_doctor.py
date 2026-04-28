import shutil
import unittest
import uuid
from pathlib import Path

from agent_system.config import Settings
from agent_system.doctor import (
    _check_backend_readiness,
    _classify_probe_failure,
    format_doctor_report,
    write_doctor_report,
)


class DoctorTests(unittest.TestCase):
    def test_classify_quota_failure_as_warning(self) -> None:
        result = _classify_probe_failure("Claude live probe", "You've hit your usage limit.")
        self.assertEqual(result.status, "warn")

    def test_backend_readiness_requires_full_cli_pair(self) -> None:
        settings = Settings(
            backend="cli",
            fast_mode=False,
            openai_api_key=None,
            anthropic_api_key=None,
            openai_model="gpt-4o",
            anthropic_model="sonnet",
            codex_model=None,
            claude_cli_path=None,
            codex_cli_path=None,
            cli_timeout_seconds=300,
            execution_timeout_seconds=8,
            max_debug_iterations=3,
        )
        result = _check_backend_readiness(settings, claude_path="claude.exe", codex_path=None)
        self.assertEqual(result.status, "fail")

    def test_format_doctor_report_includes_header(self) -> None:
        settings = Settings(
            backend="auto",
            fast_mode=True,
            openai_api_key=None,
            anthropic_api_key=None,
            openai_model="gpt-4o",
            anthropic_model="sonnet",
            codex_model=None,
            claude_cli_path=None,
            codex_cli_path=None,
            cli_timeout_seconds=300,
            execution_timeout_seconds=8,
            max_debug_iterations=3,
        )
        text = format_doctor_report(settings, [], live=False)
        self.assertIn("=== DOCTOR ===", text)
        self.assertIn("backend=auto", text)

    def test_write_doctor_report_json(self) -> None:
        settings = Settings(
            backend="auto",
            fast_mode=False,
            openai_api_key=None,
            anthropic_api_key=None,
            openai_model="gpt-4o",
            anthropic_model="sonnet",
            codex_model=None,
            claude_cli_path=None,
            codex_cli_path=None,
            cli_timeout_seconds=300,
            execution_timeout_seconds=8,
            max_debug_iterations=3,
        )
        root = Path.cwd() / ".test_doctor" / uuid.uuid4().hex
        root.mkdir(parents=True, exist_ok=False)
        self.addCleanup(shutil.rmtree, root, True)
        output = root / "doctor.json"

        write_doctor_report(
            output,
            settings=settings,
            results=[],
            live=False,
        )

        self.assertTrue(output.exists())
        self.assertIn('"backend": "auto"', output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
