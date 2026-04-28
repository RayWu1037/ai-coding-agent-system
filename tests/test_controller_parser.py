import unittest

from agent_system.controller import build_parser


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


if __name__ == "__main__":
    unittest.main()
