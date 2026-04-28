import unittest

from agent_system.task_profiles import (
    coder_guidance,
    debugger_guidance,
    is_knowledge_base_task,
    reviewer_guidance,
)


class TaskProfileTests(unittest.TestCase):
    def test_detects_knowledge_base_task(self) -> None:
        task = (
            "Write a minimal Python project for an Obsidian-style knowledge-base ingester. "
            "It should process files from a raw folder and generate wiki markdown notes."
        )
        self.assertTrue(is_knowledge_base_task(task))

    def test_non_knowledge_base_task_has_no_special_guidance(self) -> None:
        task = "Build a command-line todo app with unit tests."
        self.assertFalse(is_knowledge_base_task(task))
        self.assertEqual(coder_guidance(task), "")
        self.assertEqual(debugger_guidance(task), "")
        self.assertEqual(reviewer_guidance(task), "")

    def test_knowledge_base_task_gets_special_guidance(self) -> None:
        task = "Build an Obsidian wiki ingester for a raw folder."
        self.assertIn("top-level H1", coder_guidance(task))
        self.assertIn("real note title", debugger_guidance(task))
        self.assertIn("title", reviewer_guidance(task).lower())


if __name__ == "__main__":
    unittest.main()
