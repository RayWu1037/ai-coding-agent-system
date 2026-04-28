# Prompting Guide for AI-Assisted Project Building

## Purpose

This guide captures the prompt patterns that worked best while building and hardening the local multi-agent coding system.

It is designed for:

- reducing avoidable model errors
- reducing token waste
- making generated code easier to validate

## Core Rule

Treat prompts as engineering specifications, not casual requests.

Good prompts specify:

- task
- runtime boundary
- acceptance criteria
- prohibited failure modes
- output format

## Prompt Template 1: Minimal Build

Use this when the task is project-shaped but you want the smallest reliable first version.

```text
Build the smallest runnable local implementation for [task].
Prefer one Python file unless multiple files are strictly necessary.
Use standard-library code unless an external dependency is clearly required.
Return only runnable Python code.
```

Why it works:

- cuts scope
- reduces planning bloat
- reduces over-engineering

## Prompt Template 2: Local-Only Constraint

Use this when you want to prevent the model from escaping into hosted APIs or key-based shortcuts.

```text
Prefer a fully local implementation.
Do not require API keys, hosted services, or paid external dependencies unless explicitly requested.
```

Why it works:

- prevents fake convenience
- avoids hidden setup burden
- makes execution reproducible

## Prompt Template 3: Artifact Fidelity Constraint

Use this when generated output must preserve some structural property from source data.

```text
Preserve the first top-level H1 as the note title.
If no H1 exists, fall back to the filename stem.
Do not replace a valid document title with a lower subsection heading.
```

Why it works:

- turns vague quality preference into a hard rule

## Prompt Template 4: Negative Constraint Prompt

Use this when the model keeps producing the same ugly or invalid artifacts.

```text
Do not emit malformed wiki links.
Do not output duplicate labels.
Do not promote generic headings such as Core Idea, Notes, or Summary into concepts.
```

Why it works:

- models often respond better to explicit exclusions than to generic quality requests

## Prompt Template 5: Deterministic Parsing Prompt

Use this when the task involves parsing, transformation, extraction, or formatting.

```text
Prefer conservative, predictable logic over clever heuristics.
Avoid multiline regex overreach and brittle parsing behavior.
Use deterministic transformations where possible.
```

Why it works:

- reduces fragile parser designs
- improves debuggability

## Prompt Template 6: Repair Prompt

Use this after you already have validator or runtime failures.

```text
Original task:
[task]

Current code:
[code]

Program stdout:
[stdout]

Program stderr:
[stderr]

Validator or reviewer feedback:
[feedback]

Fix the code and return the full corrected Python file.
```

Why it works:

- focuses the model on delta repair rather than regrowth
- makes token use more efficient than repeating the whole task from scratch

## Prompt Template 7: Token-Efficient Planner Prompt

Use this before coding, but keep the plan short.

```text
Provide a concise implementation plan with at most 4-6 numbered steps.
Keep every step short.
Return plain text with numbered steps only.
```

Why it works:

- prevents oversized planner output
- keeps coder context tighter

## What To Avoid

### Avoid broad ambition with no constraints

Bad:

```text
Build a professional full-stack system for ...
```

Why bad:

- too much ambiguity
- invites architecture sprawl
- burns tokens on assumptions

### Avoid "make it better" with no error signal

Bad:

```text
Improve this code.
```

Why bad:

- no target
- no acceptance rule
- no repair direction

### Avoid asking for explanation and code together when automation matters

Bad:

```text
Explain your reasoning and then provide the code.
```

Why bad:

- increases token cost
- creates noise when code needs to be executed automatically

## Recommended Student Workflow

1. Write the narrowest acceptable task statement.
2. Add the local-only constraint.
3. Add 1-3 hard failure prohibitions.
4. Ask for short plan only.
5. Compress the plan if needed.
6. Ask for code only.
7. Run the code.
8. Feed exact validator/runtime failures back into repair prompt.

## Example Prompt Used Successfully

```text
Write a minimal Python project for an Obsidian-style knowledge-base ingester.
It should process files from a raw folder, track processed files, and generate wiki markdown notes with [[links]] for concepts and summaries.
Prefer a local-only implementation.
Preserve the first H1 as the note title.
Reject generic concepts such as Core Idea, Notes, and Summary.
Return only runnable Python code.
```

## Final Principle

The best prompt is usually not the most detailed one.

It is the one that:

- removes ambiguity
- sets boundaries
- names failure modes
- minimizes unnecessary prose
