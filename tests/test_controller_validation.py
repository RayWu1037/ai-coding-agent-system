import unittest
import uuid
import shutil
from pathlib import Path

from agent_system.controller import _inspect_knowledge_base_artifacts


class ControllerValidationTests(unittest.TestCase):
    def _make_test_root(self) -> Path:
        root = Path.cwd() / ".test_controller_validation"
        root.mkdir(exist_ok=True)
        test_dir = root / uuid.uuid4().hex
        test_dir.mkdir()
        self.addCleanup(shutil.rmtree, test_dir, True)
        return test_dir

    def test_inspect_knowledge_base_artifacts_accepts_clean_output(self) -> None:
        test_root = self._make_test_root()
        notes_dir = test_root / "notes"
        notes_dir.mkdir()
        (notes_dir / "AI Agent.md").write_text(
            "\n".join(
                [
                    "# AI Agent",
                    "",
                    "## Summary",
                    "",
                    "An AI Agent turns Raw Notes into Wiki Notes inside an Obsidian vault.",
                    "",
                    "## Concepts",
                    "",
                    "[[AI Agent]] - [[Raw Notes]] - [[Wiki Notes]]",
                ]
            ),
            encoding="utf-8",
        )
        (notes_dir / "Index.md").write_text("- [[AI Agent]]\n", encoding="utf-8")

        self.assertEqual(_inspect_knowledge_base_artifacts(test_root), [])

    def test_inspect_knowledge_base_artifacts_flags_title_drift_and_noise(self) -> None:
        test_root = self._make_test_root()
        notes_dir = test_root / "notes"
        notes_dir.mkdir()
        (notes_dir / "Core Idea.md").write_text(
            "\n".join(
                [
                    "# Core Idea",
                    "",
                    "## Concepts",
                    "",
                    "[[AI Agent]] - [[Notes. Concept]] - [[Core Idea]]",
                ]
            ),
            encoding="utf-8",
        )
        (notes_dir / "Index.md").write_text("- [[Core Idea]]\n", encoding="utf-8")

        errors = _inspect_knowledge_base_artifacts(test_root)

        self.assertTrue(any("AI Agent.md" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
