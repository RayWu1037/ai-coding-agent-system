import json
import shutil
import unittest
import uuid
from pathlib import Path

from agent_system.wiki_ingester import WikiSettings, extract_concepts, ingest


class WikiIngesterTests(unittest.TestCase):
    def _make_test_root(self) -> Path:
        root = Path.cwd() / ".test_wiki_ingester"
        root.mkdir(exist_ok=True)
        test_dir = root / uuid.uuid4().hex
        test_dir.mkdir()
        self.addCleanup(shutil.rmtree, test_dir, True)
        return test_dir

    def test_extract_concepts_prefers_specific_phrases(self) -> None:
        title = "Anthropic Prompt Engineering Overview"
        body = (
            "Anthropic's prompt engineering overview says prompt optimization should begin "
            "with clear success criteria and some way to test results empirically. "
            "It also recommends direct instructions, examples when needed, and structured prompting."
        )

        concepts = extract_concepts(title, body)

        self.assertNotIn("Anthropic Prompt Engineering Overview", concepts)
        self.assertNotIn("Anthropic Prompt Engineering", concepts)
        self.assertIn("Direct Instructions", concepts)
        self.assertNotIn("Prompt", concepts)
        self.assertNotIn("Source", concepts)
        self.assertNotIn("Docs", concepts)

    def test_ingest_generates_notes_and_filtered_concepts(self) -> None:
        test_root = self._make_test_root()
        raw_dir = test_root / "raw"
        notes_dir = test_root / "notes"
        state_path = test_root / "state.json"
        raw_dir.mkdir()

        (raw_dir / "openai_prompt_engineering.md").write_text(
            "\n".join(
                [
                    "# OpenAI Prompt Engineering Guide",
                    "",
                    "The OpenAI prompt engineering guide explains that better results come from clear instructions,",
                    "explicit output expectations, and iterative refinement.",
                    "",
                    "Official source: https://example.com",
                ]
            ),
            encoding="utf-8",
        )

        processed = ingest(
            WikiSettings(raw_dir=raw_dir, notes_dir=notes_dir, state_path=state_path)
        )

        self.assertEqual(processed, 1)
        note = (notes_dir / "OpenAI Prompt Engineering Guide.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('  - "OpenAI Prompt Engineering"', note)
        self.assertIn("## Aliases", note)
        self.assertIn("[[Iterative Refinement]]", note)
        self.assertNotIn("[[OpenAI Prompt Engineering Guide]]", note)
        self.assertNotIn("[[OpenAI Prompt Engineering]]", note)
        self.assertNotIn("[[Prompt]]", note)
        self.assertNotIn("[[Source]]", note)

        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertIn("openai_prompt_engineering.md", state["files"])
        self.assertTrue((notes_dir / "Index.md").exists())


if __name__ == "__main__":
    unittest.main()
