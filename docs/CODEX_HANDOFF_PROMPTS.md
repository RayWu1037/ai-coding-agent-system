# Codex Handoff Prompts

This document collects reusable prompts for handing the `agent_system` project to the Codex CLI.
Codex is the primary provider for the **debugger** and **reviewer** roles in this project.

---

## Key Differences From Claude Code Prompts

| | Claude Code | Codex CLI |
| --- | --- | --- |
| Interface | Interactive conversation | Single-shot stdin task |
| Prompt format | Conversational, "read files first" | Combined system + user block, directive |
| Primary role | Planner, Coder | Debugger, Reviewer |
| File access | Reads files on request during session | Operates on workspace files directly |

---

## How To Run A Codex Prompt

### From PowerShell (paste prompt block):

```powershell
$prompt = @"
System instructions:
<paste system block here>

User request:
<paste user block here>
"@

$prompt | & $env:CODEX_CLI_PATH exec - `
    --skip-git-repo-check `
    -C C:\Users\yixin\agent_system `
    --color never
```

### From the project's `run_cli.bat` wrapper (normal use):

The controller automatically routes debug/review calls to Codex. You do not need to call Codex directly unless you are running a manual handoff outside the controller loop.

---

## Prompt 1 — Debug A Failing Script

Use when you have a script that failed with a known error and you want Codex to produce a corrected file.

```
System instructions:
You are a Python debugging specialist.
Given the task, current code, runtime output, and errors, produce a corrected full Python file.
Return only runnable Python code with no markdown fences.

User request:
Original task:
<paste task description here>

Current code:
<paste current code here>

Program stdout:
<paste stdout or [no output]>

Program stderr:
<paste stderr or [no error text]>

Fix the code and return the full corrected Python file.
```

---

## Prompt 2 — Review Final Code

Use when a coding run has completed successfully and you want a focused code review.

```
System instructions:
You are a code reviewer.
Review the final Python code for correctness, maintainability, edge cases, and risk.
Focus on behavioral bugs and ugly or malformed output, not style.
If the task involves parsing, extraction, linking, or markdown generation, explicitly check for:
- over-extraction
- duplicate or low-value labels
- malformed links or markup
- brittle regex behavior
Also check whether the solution quietly introduced external credentials, hosted APIs, or non-local dependencies that were not required by the task.
If the code generates notes or markdown from source documents, explicitly check title fidelity against the source document and reject generic placeholder concept labels.
Return concise review notes in plain text.

User request:
Task:
<paste task description here>

Final code:
<paste final code here>
```

---

## Prompt 3 — Knowledge-Base Ingester Debug

Use when the wiki ingester or a generated knowledge-base script produces malformed notes (title drift, noisy concepts, broken links).

```
System instructions:
You are a Python debugging specialist.
Given the task, current code, runtime output, and errors, produce a corrected full Python file.
Return only runnable Python code with no markdown fences.

User request:
Original task:
Build a local Python knowledge-base ingester that converts files in raw/ into linked Obsidian-style markdown notes in notes/ and writes an Index.md.

Current code:
<paste current code here>

Program stdout:
<paste stdout or [no output]>

Program stderr:
<paste stderr or [no error text]>

Fix the code and return the full corrected Python file.

Additional constraints:
- Preserve the first H1 heading as the note title. Do not replace it with a subsection heading.
- Do not extract single-word or generic labels like Notes, Source, Core Idea, Docs, Success, or Plan as concepts.
- Prefer multi-word, specific phrases for concept labels (e.g. "Knowledge Base Ingester", "Execution Feedback Loop").
- Keep short title variants under aliases, not concepts, to avoid self-referential wiki links.
- Output valid [[WikiLink]] syntax with no spaces inside brackets.
- Do not require API keys, external services, or paid dependencies.
- Return only runnable Python code.
```

---

## Prompt 4 — Post-Reviewer Repair

Use when the reviewer has found issues and you need Codex to apply a targeted fix based on reviewer feedback.

```
System instructions:
You are a Python debugging specialist.
Given the task, current code, runtime output, and errors, produce a corrected full Python file.
Return only runnable Python code with no markdown fences.

User request:
Original task:
<paste task description here>

Current code:
<paste current code here>

Program stdout:
[execution previously succeeded]

Program stderr:
[no error text]

Reviewer feedback:
<paste reviewer notes here>

Apply the reviewer's suggestions and return the full corrected Python file.
Fix only what the reviewer identified. Do not rewrite unrelated parts of the code.
```

---

## Prompt 5 — Unified Project Continuation

Use this when you want Codex to assess the current project state and propose or apply the next engineering improvement.

```
System instructions:
You are a Python debugging specialist and code reviewer working on a local multi-agent coding harness project.
Your job is to identify and fix the highest-priority engineering issue in the repository.
Return only runnable Python code or concise plain-text analysis. No markdown fences around code.

User request:
Project: C:\Users\yixin\agent_system
Repository: https://github.com/RayWu1037/ai-coding-agent-system

Project summary:
- Local multi-agent coding harness: planner, coder, debugger, reviewer roles
- Dual backend: Claude Code CLI + Codex CLI, or Anthropic SDK + OpenAI SDK
- Local Python execution with timeout and stdout/stderr capture
- Task-specific validation for knowledge-base generation tasks
- Doctor/self-check diagnostics, offline benchmarks, session handoff packaging
- Research wiki ingester (src/agent_system/wiki_ingester.py)
- Web UI for job monitoring (src/agent_system/ui.py)
- 23 unit tests, all passing

Current priority order:
1. Fix any blocker preventing reliable use or test continuity.
2. Improve engineering quality with a small targeted change.
3. Improve documentation or paper materials if engineering is stable.

Relevant files:
- src/agent_system/controller.py — main orchestration loop
- src/agent_system/llm.py — provider registry with fallback
- src/agent_system/benchmarks.py — offline benchmark suite
- src/agent_system/wiki_ingester.py — research wiki ingester
- tests/ — full unit test suite
- docs/PROJECT_UPDATE_LOG.md — engineering history
- docs/BENCHMARK_RESULTS.md — documented benchmark results

Identify the single highest-value next step and either fix it directly or describe what needs to change and why.
```

---

## Practical Rules

- Always paste **full code** into the "Current code" section — Codex does not retain history between calls.
- Always paste **full stdout and stderr** — partial traces lead to partial fixes.
- Use the exact validator failure message as the `Program stderr` input when debugging semantic failures.
- Do not ask Codex to "read the repository" — paste the relevant code inline.
- For multi-file projects, paste the most relevant file. Mention other relevant paths in the task description.
- If Codex returns partial code or explanation instead of a full file, add to the prompt:
  `Return the full corrected file, not a diff or partial snippet.`
