from __future__ import annotations

from pathlib import Path


def knowledge_base_validation_sample() -> str:
    return """# AI Agent

An AI Agent can turn raw notes into linked wiki notes inside an Obsidian knowledge base.

## Core Idea

The system reads files from a raw folder, extracts stable concepts, and writes markdown notes with [[links]] into a wiki vault.

## Output Expectations

The generated note should keep the top-level title AI Agent and avoid generic concepts like Core Idea or Notes.
"""


def inspect_knowledge_base_artifacts(root_dir: Path) -> list[str]:
    note_path = find_generated_note(root_dir, "AI Agent.md")
    index_path = find_generated_index(root_dir)
    note_files = sorted(
        path.name
        for path in root_dir.rglob("*.md")
        if path.name.lower() not in {"_index.md", "index.md"}
    )
    errors: list[str] = []

    if note_path is None:
        errors.append(
            "expected an output note named 'AI Agent.md' derived from the sample file's top-level H1; "
            f"found: {', '.join(note_files) if note_files else 'no note files'}"
        )
        return errors

    note_text = note_path.read_text(encoding="utf-8", errors="replace")
    if "# AI Agent" not in note_text:
        errors.append("generated note does not preserve the source title 'AI Agent' as the main H1")
    if "[[Notes. Concept]]" in note_text:
        errors.append("generated note contains malformed or low-value concept label 'Notes. Concept'")
    if "[[Core Idea]]" in note_text:
        errors.append("generated note promoted the generic subsection heading 'Core Idea' into a concept link")
    lowered_note = note_text.casefold()
    if "raw notes" not in lowered_note or "wiki notes" not in lowered_note:
        errors.append("generated note summary/body did not preserve the core relation between Raw Notes and Wiki Notes")

    if index_path is None:
        errors.append("knowledge-base index file was not created")
        return errors

    index_text = index_path.read_text(encoding="utf-8", errors="replace")
    if "[[AI Agent]]" not in index_text:
        errors.append("knowledge-base index does not link to [[AI Agent]]")
    return errors


def find_generated_note(root_dir: Path, filename: str) -> Path | None:
    preferred_dirs = ["vault", "wiki", "notes"]
    for directory_name in preferred_dirs:
        candidate = root_dir / directory_name / filename
        if candidate.exists():
            return candidate
    for candidate in root_dir.rglob(filename):
        if candidate.is_file():
            return candidate
    return None


def find_generated_index(root_dir: Path) -> Path | None:
    for directory_name in ["vault", "wiki", "notes"]:
        for filename in ["_index.md", "Index.md", "index.md"]:
            candidate = root_dir / directory_name / filename
            if candidate.exists():
                return candidate
    for filename in ["_index.md", "Index.md", "index.md"]:
        candidate = root_dir / filename
        if candidate.exists():
            return candidate
    return None
