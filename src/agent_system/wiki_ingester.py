from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WikiSettings:
    raw_dir: Path
    notes_dir: Path
    state_path: Path
    allowed_extensions: tuple[str, ...] = (".txt", ".md", ".markdown")


@dataclass
class ParsedDocument:
    title: str
    body: str
    aliases: list[str]
    concepts: list[str]
    summary: str


GENERIC_LABELS = {
    "abstract",
    "appendix",
    "article",
    "background",
    "concept",
    "concepts",
    "conclusion",
    "configuration",
    "content",
    "contents",
    "context",
    "core idea",
    "details",
    "discussion",
    "doc",
    "docs",
    "document",
    "documents",
    "example",
    "examples",
    "guide",
    "idea",
    "index",
    "introduction",
    "key point",
    "key points",
    "main idea",
    "note",
    "notes",
    "official source",
    "overview",
    "page",
    "paper",
    "project",
    "prompt",
    "reference",
    "references",
    "related",
    "requirements",
    "section",
    "source",
    "spec",
    "summary",
    "success",
    "system",
    "takeaway",
    "takeaways",
    "task",
    "todo",
    "workflow",
    "workflows",
    "work",
}

STOP_WORDS = {
    "a",
    "about",
    "after",
    "again",
    "against",
    "all",
    "also",
    "an",
    "and",
    "among",
    "another",
    "are",
    "as",
    "at",
    "be",
    "because",
    "before",
    "being",
    "between",
    "both",
    "but",
    "by",
    "can",
    "clear",
    "come",
    "could",
    "during",
    "each",
    "every",
    "for",
    "first",
    "from",
    "have",
    "into",
    "its",
    "like",
    "more",
    "most",
    "needed",
    "not",
    "of",
    "on",
    "or",
    "other",
    "our",
    "over",
    "same",
    "should",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "under",
    "useful",
    "using",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
    "your",
}

TITLE_SUFFIX_WORDS = {
    "config",
    "configuration",
    "guide",
    "overview",
    "requirements",
}

LOW_SIGNAL_PHRASE_WORDS = GENERIC_LABELS | {
    "better",
    "build",
    "engineering",
    "explicit",
    "good",
    "improvement",
    "iterative",
    "local",
    "narrower",
    "official",
    "project",
    "quality",
    "reduce",
    "reliable",
    "supports",
}

HELPER_WORDS = {
    "behaves",
    "begin",
    "begins",
    "build",
    "comes",
    "define",
    "defines",
    "empirically",
    "explains",
    "help",
    "helps",
    "improves",
    "including",
    "matches",
    "means",
    "recommends",
    "reduce",
    "reduces",
    "relies",
    "says",
    "show",
    "shows",
    "supports",
    "test",
    "use",
    "uses",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m agent_system.wiki_ingester",
        description="Ingest raw markdown/text sources into a local wiki note set.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory containing raw/, notes/, and state.json.",
    )
    parser.add_argument("--raw-dir", help="Override raw input directory.")
    parser.add_argument("--notes-dir", help="Override generated notes directory.")
    parser.add_argument("--state-path", help="Override state file path.")
    return parser


def settings_from_args(args: argparse.Namespace) -> WikiSettings:
    root = Path(args.root).resolve()
    raw_dir = Path(args.raw_dir).resolve() if args.raw_dir else root / "raw"
    notes_dir = Path(args.notes_dir).resolve() if args.notes_dir else root / "notes"
    state_path = (
        Path(args.state_path).resolve() if args.state_path else root / "state.json"
    )
    return WikiSettings(raw_dir=raw_dir, notes_dir=notes_dir, state_path=state_path)


def ensure_paths(settings: WikiSettings) -> None:
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    settings.notes_dir.mkdir(parents=True, exist_ok=True)
    settings.state_path.parent.mkdir(parents=True, exist_ok=True)
    if not settings.state_path.exists():
        save_state(settings.state_path, {"files": {}})


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"files": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"files": {}}
    if not isinstance(data, dict):
        return {"files": {}}
    if not isinstance(data.get("files"), dict):
        data["files"] = {}
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_key(raw_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(raw_dir.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def note_exists(settings: WikiSettings, record: dict[str, Any]) -> bool:
    note_name = record.get("note")
    if not isinstance(note_name, str) or not note_name:
        return False
    return (settings.notes_dir / note_name).is_file()


def scan_new_files(settings: WikiSettings, state: dict[str, Any]) -> list[tuple[Path, str]]:
    results: list[tuple[Path, str]] = []
    recorded = state.get("files", {})
    if not isinstance(recorded, dict):
        recorded = {}

    for path in sorted(settings.raw_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in settings.allowed_extensions:
            continue
        digest = file_hash(path)
        key = source_key(settings.raw_dir, path)
        record = recorded.get(key, {})
        if not isinstance(record, dict):
            record = {}
        if record.get("sha256") == digest and note_exists(settings, record):
            continue
        results.append((path, digest))

    return results


def read_text_file(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def parse_document(path: Path) -> ParsedDocument:
    text = read_text_file(path).replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    title = ""
    title_line_index: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            candidate = clean_inline_text(stripped[2:])
            if candidate:
                title = candidate
                title_line_index = index
                break

    if not title:
        title = clean_inline_text(path.stem) or "Untitled"

    body_lines = []
    for index, line in enumerate(lines):
        if index == title_line_index:
            continue
        body_lines.append(line.rstrip())
    body = "\n".join(body_lines).strip()

    aliases = derive_aliases(title)
    concepts = extract_concepts(title, body)
    summary = summarize(body)
    return ParsedDocument(
        title=title,
        body=body,
        aliases=aliases,
        concepts=concepts,
        summary=summary,
    )


def clean_inline_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    text = re.sub(r"\[([^\]\n]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[\[([^|\]\n]+)\|([^\]\n]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]\n]+)\]\]", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \t#-*_:;,.!?\"'")


def plain_text(markdown: str) -> str:
    out: list[str] = []
    in_fence = False
    for raw_line in markdown.split("\n"):
        line = raw_line.strip()
        if line.startswith("```") or line.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith(">"):
            line = line.lstrip("> ").strip()
        line = re.sub(r"!\[[^\]\n]*\]\([^)]+\)", "", line)
        line = re.sub(r"\[([^\]\n]+)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"\[\[([^|\]\n]+)\|([^\]\n]+)\]\]", r"\2", line)
        line = re.sub(r"\[\[([^\]\n]+)\]\]", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        line = re.sub(r"[*_~]", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            out.append(line)
    return " ".join(out)


def summarize(body: str, max_sentences: int = 3, max_chars: int = 600) -> str:
    text = plain_text(body)
    if not text:
        return "No summary available."

    sentences = split_sentences(text)
    selected = []
    total = 0
    for sentence in sentences:
        if sentence.lower().startswith("official source:"):
            continue
        if len(sentence) < 20 and selected:
            continue
        if total + len(sentence) + 1 > max_chars:
            break
        selected.append(sentence)
        total += len(sentence) + 1
        if len(selected) >= max_sentences:
            break

    if selected:
        return " ".join(selected)
    trimmed = text[:max_chars].rstrip()
    return trimmed + ("..." if len(text) > max_chars else "")


def split_sentences(text: str) -> list[str]:
    sentences = []
    start = 0
    for index, char in enumerate(text):
        if char not in ".!?":
            continue
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if next_char and not next_char.isspace():
            continue
        sentence = text[start : index + 1].strip()
        if sentence:
            sentences.append(sentence)
        start = index + 1
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def extract_concepts(title: str, body: str, limit: int = 6) -> list[str]:
    candidates: list[str] = []

    for heading in extract_heading_candidates(body):
        normalized = normalize_concept(heading)
        if normalized:
            candidates.append(normalized)

    body_text = plain_text(body)
    for phrase in extract_phrases(body_text):
        normalized = normalize_concept(phrase)
        if normalized:
            candidates.append(normalized)

    seen = set()
    concepts: list[str] = []
    for candidate in candidates:
        key = candidate.casefold()
        if key in seen:
            continue
        seen.add(key)
        concepts.append(candidate)
        if len(concepts) >= limit:
            break
    return concepts


def title_variants(title: str) -> list[str]:
    clean = clean_inline_text(title)
    if not clean:
        return []
    words = [word for word in re.split(r"\s+", clean) if word]
    variants = [clean]
    if len(words) >= 2 and words[-1].casefold() in TITLE_SUFFIX_WORDS:
        trimmed = " ".join(words[:-1]).strip()
        if trimmed:
            variants.append(trimmed)
    return variants


def derive_aliases(title: str) -> list[str]:
    variants = title_variants(title)
    if len(variants) <= 1:
        return []
    seen = {variants[0].casefold()}
    aliases: list[str] = []
    for variant in variants[1:]:
        key = variant.casefold()
        if key in seen:
            continue
        seen.add(key)
        aliases.append(variant)
    return aliases


def extract_heading_candidates(body: str) -> list[str]:
    candidates: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        heading = clean_inline_text(stripped.lstrip("#").strip())
        if word_count(heading) >= 2:
            candidates.append(heading)
    return candidates


def extract_phrases(text: str) -> list[str]:
    cleaned = text.replace("/", " ").replace("-", " ")
    chunks = re.split(r"[.;:()\[\]]", cleaned)
    scores: dict[str, int] = {}
    for chunk in chunks:
        for phrase in phrase_candidates_from_chunk(chunk):
            scores[phrase] = scores.get(phrase, 0) + 1

    ranked = sorted(
        scores.items(),
        key=lambda item: (-item[1], -word_count(item[0]), item[0].casefold()),
    )
    return [phrase for phrase, _ in ranked]


def phrase_candidates_from_chunk(chunk: str) -> list[str]:
    stripped = chunk.strip()
    if not stripped or stripped.lower().startswith("official source"):
        return []
    phrases: list[str] = []
    for segment in re.split(r",|\band\b|\bor\b", stripped, flags=re.IGNORECASE):
        words = re.findall(r"[A-Za-z][A-Za-z0-9']*", segment)
        if len(words) < 2:
            continue
        lowered = [word.casefold() for word in words]

        start = 0
        end = len(words)
        while start < end and lowered[start] in STOP_WORDS | HELPER_WORDS:
            start += 1
        while end > start and lowered[end - 1] in STOP_WORDS | HELPER_WORDS:
            end -= 1
        if end - start < 2:
            continue

        candidate_words = words[start:end]
        candidate_lower = lowered[start:end]
        if len(candidate_words) > 4:
            candidate_words = candidate_words[-3:]
            candidate_lower = candidate_lower[-3:]
            while candidate_words and candidate_lower[0] in STOP_WORDS | HELPER_WORDS:
                candidate_words = candidate_words[1:]
                candidate_lower = candidate_lower[1:]
            while candidate_words and candidate_lower[-1] in STOP_WORDS | HELPER_WORDS:
                candidate_words = candidate_words[:-1]
                candidate_lower = candidate_lower[:-1]
            if len(candidate_words) < 2:
                continue

        if any(word in HELPER_WORDS for word in candidate_lower):
            continue
        if any(word in GENERIC_LABELS for word in candidate_lower):
            continue
        if all(word in LOW_SIGNAL_PHRASE_WORDS for word in candidate_lower):
            continue

        phrase = " ".join(candidate_words)
        normalized = normalize_concept(phrase, allow_single_word=False)
        if normalized:
            phrases.append(normalized)
    return phrases


def normalize_concept(
    text: str,
    allow_single_word: bool = False,
    from_title: bool = False,
) -> str:
    text = clean_inline_text(text)
    if not text or "\n" in text or "\r" in text:
        return ""
    if "[[" in text or "]]" in text or "[" in text or "]" in text:
        return ""

    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 64:
        return ""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9' -]*[A-Za-z0-9]?", text):
        return ""

    words = [word for word in re.split(r"[ -]+", text) if word]
    if not words:
        return ""
    if len(words) == 1 and not allow_single_word and not text.isupper():
        return ""
    if len(words) > 5:
        return ""
    if any(len(word) > 24 for word in words):
        return ""

    lowered_words = [word.casefold() for word in words]
    normalized_label = " ".join(lowered_words)
    if normalized_label in GENERIC_LABELS:
        return ""
    if all(word in STOP_WORDS for word in lowered_words):
        return ""
    if not from_title and any(word in GENERIC_LABELS for word in lowered_words):
        return ""
    if from_title and all(word in GENERIC_LABELS for word in lowered_words):
        return ""
    if len("".join(words)) < 6:
        return ""

    return " ".join(format_concept_word(word) for word in words)


def word_count(text: str) -> int:
    return len([word for word in re.split(r"[ -]+", text.strip()) if word])


def format_concept_word(word: str) -> str:
    if word.isupper() and len(word) <= 6:
        return word
    if any(char.isupper() for char in word[1:]):
        return word
    if any(char.isdigit() for char in word):
        return word
    return word[:1].upper() + word[1:].lower()


def safe_note_filename(title: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title)
    name = re.sub(r"\s+", " ", name).strip().rstrip(".")
    if not name:
        name = "Untitled"
    return f"{name[:80]}.md"


def unique_note_path(notes_dir: Path, title: str, source: str) -> Path:
    base_name = safe_note_filename(title)
    note_path = notes_dir / base_name
    if not note_path.exists():
        return note_path

    source_slug = re.sub(r"[^A-Za-z0-9]+", "-", Path(source).stem).strip("-")
    if not source_slug:
        source_slug = hashlib.sha1(source.encode("utf-8")).hexdigest()[:8]

    stem = note_path.stem[:70].rstrip()
    candidate = notes_dir / f"{stem} - {source_slug[:20]}.md"
    counter = 2
    while candidate.exists():
        candidate = notes_dir / f"{stem} - {source_slug[:16]} {counter}.md"
        counter += 1
    return candidate


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def wiki_link(concept: str) -> str:
    clean = clean_inline_text(concept)
    if not clean or "[" in clean or "]" in clean:
        return ""
    return f"[[{clean}]]"


def generate_note(parsed: ParsedDocument, source_path: Path, digest: str, raw_dir: Path) -> str:
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source = source_key(raw_dir, source_path)
    links = [link for concept in parsed.concepts if (link := wiki_link(concept))]

    frontmatter = [
        "---",
        f"title: {yaml_string(parsed.title)}",
        f"source: {yaml_string(source)}",
        f"source_sha256: {yaml_string(digest)}",
        f"ingested_at: {yaml_string(created_at)}",
        "aliases:",
    ]
    for alias in parsed.aliases:
        frontmatter.append(f"  - {yaml_string(alias)}")
    frontmatter.extend(
        [
        "concepts:",
        ]
    )
    for concept in parsed.concepts:
        frontmatter.append(f"  - {yaml_string(concept)}")
    frontmatter.append("---")

    sections = [
        "\n".join(frontmatter),
        f"# {parsed.title}",
        "## Summary",
        parsed.summary,
        "## Source",
        f"- File: `{source}`",
        f"- SHA-256: `{digest}`",
    ]
    if parsed.aliases:
        sections.extend(["## Aliases", ", ".join(f"`{alias}`" for alias in parsed.aliases)])
    if links:
        sections.extend(["## Concepts", ", ".join(links)])
    return "\n\n".join(sections).rstrip() + "\n"


def generate_index(state: dict[str, Any]) -> str:
    records = []
    files = state.get("files", {})
    if isinstance(files, dict):
        for source, record in files.items():
            if not isinstance(record, dict):
                continue
            note_title = record.get("note_title") or record.get("title")
            if not isinstance(note_title, str) or not note_title:
                continue
            records.append((note_title.casefold(), note_title, source))

    lines = [
        "# Knowledge Base Index",
        "",
        "## Notes",
    ]
    if not records:
        lines.extend(["", "No notes ingested yet."])
    else:
        for _, note_title, source in sorted(records):
            lines.append(f"- [[{note_title}]] - `{source}`")
    return "\n".join(lines).rstrip() + "\n"


def ingest(settings: WikiSettings) -> int:
    ensure_paths(settings)
    state = load_state(settings.state_path)
    state.setdefault("files", {})
    processed = 0

    for path, digest in scan_new_files(settings, state):
        parsed = parse_document(path)
        key = source_key(settings.raw_dir, path)

        old_record = state["files"].get(key, {})
        old_note = old_record.get("note") if isinstance(old_record, dict) else None
        if isinstance(old_note, str) and old_note:
            note_path = settings.notes_dir / old_note
        else:
            note_path = unique_note_path(settings.notes_dir, parsed.title, key)

        note_path.write_text(
            generate_note(parsed, path, digest, settings.raw_dir),
            encoding="utf-8",
        )
        state["files"][key] = {
            "sha256": digest,
            "note": note_path.name,
            "note_title": parsed.title,
            "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        processed += 1

    (settings.notes_dir / "Index.md").write_text(
        generate_index(state),
        encoding="utf-8",
    )
    save_state(settings.state_path, state)
    return processed


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = settings_from_args(args)
    processed = ingest(settings)
    print(f"Ingested {processed} file(s) into {settings.notes_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
