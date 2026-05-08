import unittest
from unittest.mock import patch

from agent_system.controller import build_parser
from agent_system.config import load_settings
from agent_system.controller import Controller


class ControllerParserTests(unittest.TestCase):
    def test_doctor_flag_parses_without_task(self) -> None:
        args = build_parser().parse_args(["--doctor"])
        self.assertTrue(args.doctor)
        self.assertIsNone(args.task)

    def test_task_still_parses_normally(self) -> None:
        args = build_parser().parse_args(["--task", "Build a todo app"])
        self.assertEqual(args.task, "Build a todo app")
        self.assertFalse(args.doctor)

    def test_session_dir_parses(self) -> None:
        args = build_parser().parse_args(
            ["--task", "Build a todo app", "--session-dir", "sessions"]
        )
        self.assertEqual(str(args.session_dir), "sessions")

    def test_accessbridge_mode_flags_parse(self) -> None:
        args = build_parser().parse_args(
            [
                "--student-mode",
                "--budget-mode",
                "--task",
                "Fix a beginner CSV todo app",
            ]
        )

        self.assertTrue(args.student_mode)
        self.assertTrue(args.budget_mode)

    def test_demo_mode_returns_agentrelay_sample_without_provider(self) -> None:
        with patch.dict("os.environ", {"AGENT_DEMO_MODE": "1"}, clear=True):
            controller = Controller()
            summary = controller.run("Fix this buggy Python CSV todo app")

        self.assertTrue(summary.success)
        self.assertIn("csv.DictReader", summary.final_code)
        self.assertIn("Google Cloud path", summary.review)

    def test_student_budget_demo_returns_learning_sections(self) -> None:
        with patch.dict("os.environ", {"AGENT_DEMO_MODE": "1"}, clear=True):
            controller = Controller()
            summary = controller.run(
                "A beginner student wrote a Python CSV todo app",
                student_mode=True,
                budget_mode=True,
            )

        self.assertTrue(summary.success)
        self.assertEqual(summary.iterations_used, 1)
        self.assertIn("What was wrong", summary.review)
        self.assertIn("What was fixed", summary.review)
        self.assertIn("What you learned", summary.review)

    def test_gemini_settings_use_standard_api_key_env(self) -> None:
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            settings = load_settings()

        self.assertTrue(settings.has_gemini)
        self.assertEqual(settings.gemini_model, "gemini-2.5-flash")

    def test_accessbridge_settings_load_from_env(self) -> None:
        with patch.dict(
            "os.environ",
            {"AGENT_STUDENT_MODE": "1", "AGENT_BUDGET_MODE": "true"},
            clear=True,
        ):
            settings = load_settings()

        self.assertTrue(settings.student_mode)
        self.assertTrue(settings.budget_mode)


if __name__ == "__main__":
    unittest.main()
