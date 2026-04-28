from __future__ import annotations


def is_knowledge_base_task(task: str) -> bool:
    normalized = task.lower()
    keywords = [
        "obsidian",
        "knowledge base",
        "knowledge-base",
        "wiki",
        "[[links]]",
        "raw folder",
        "vault",
        "markdown notes",
        "ingester",
    ]
    return sum(keyword in normalized for keyword in keywords) >= 2


def coder_guidance(task: str) -> str:
    if not is_knowledge_base_task(task):
        return ""
    return (
        "Knowledge-base task requirements:\n"
        "- Prefer a fully local implementation with no API keys.\n"
        "- When converting markdown source files into wiki notes, preserve the first top-level H1 as the note title.\n"
        "- If no H1 exists, fall back to the filename stem; never replace a valid document title with a lower subsection heading like 'Core Idea'.\n"
        "- Extract concepts conservatively. Reject generic fragments such as 'Core Idea', 'Notes', 'Summary', 'Concept', or concatenated junk labels.\n"
        "- Generate clean Obsidian-style [[links]] with no malformed brackets, duplicates, or multiline link text.\n"
        "- Prefer deterministic parsing over broad regex heuristics when title or concept quality would suffer.\n"
    )


def debugger_guidance(task: str) -> str:
    if not is_knowledge_base_task(task):
        return ""
    return (
        "Knowledge-base semantic checks to satisfy while fixing the code:\n"
        "- Keep the note title aligned with the source document's first H1.\n"
        "- Avoid generic or concatenated concept labels.\n"
        "- Ensure the generated index links to the real note title.\n"
        "- Keep all output local and runnable without external credentials.\n"
    )


def reviewer_guidance(task: str) -> str:
    if not is_knowledge_base_task(task):
        return ""
    return (
        "This task builds an Obsidian-style knowledge-base ingester.\n"
        "Check that note titles come from the source document's first H1, not a subsection heading.\n"
        "Check that extracted concepts are specific, readable, and not generic placeholders.\n"
        "Check that the summary reflects the whole source note, not only one lower section.\n"
    )
