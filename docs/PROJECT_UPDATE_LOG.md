# Project Update Log

## Phase 0: Initial Goal

Objective:

- reproduce a "Claude + Codex" style local coding-agent workflow
- make it runnable on Windows
- keep it portfolio-worthy instead of a throwaway demo

Initial structure:

- `Planner`
- `Coder`
- `Debugger`
- `Reviewer`
- `Python Executor`
- local Web UI

## Phase 1: Baseline CLI/API Harness

What was added:

- role-based controller loop
- dual backend support: CLI and SDK
- Windows launcher scripts
- basic README and GitHub publishing

Problems observed:

- deprecated Anthropic model defaults
- PowerShell shim issues
- global PATH issues
- CLI/backend setup was easy to misconfigure

Fixes:

- switched default Anthropic model away from deprecated values
- documented direct `.exe` / `.cmd` use
- improved setup docs and wrapper scripts

## Phase 2: Runtime Stability Fixes

Problems observed:

- subprocess decoding issues on Windows
- temporary-directory permission failures
- execution loop marked some runs as failed even after code had been fixed

Fixes:

- forced UTF-8 decode paths for CLI subprocess output
- moved scratch execution into project-local `.agent_system_runs`
- corrected execution/debug loop semantics

Outcome:

- simple tasks became consistently runnable

## Phase 3: Medium Task Failure on Knowledge-Base Ingestion

Stress test task:

- build an Obsidian-style knowledge-base ingester from a `raw/` folder into markdown wiki notes

Problems observed:

- planner output was too long and slowed coding
- coder timed out
- generated code sometimes used API-key backends instead of local-only logic
- generated artifacts could run but still produce bad titles and noisy concepts

Representative failure modes:

- title drift to `Core Idea`
- malformed or low-value wiki links
- noisy concepts like `Notes. Concept`
- summary focused on a subsection instead of the whole note

Fixes:

- added `fast mode`
- compacted planner output before passing it to the coder
- added smaller fallback plans for timeout recovery
- added local-only / no-key prompt constraints

Outcome:

- project-shaped tasks became more likely to complete
- quality was still inconsistent

## Phase 4: Task-Specific Quality Guardrails

Problems observed:

- executable output was still not good enough
- "success" only meant "process exited with 0"

Fixes:

- introduced `task_profiles.py`
- added knowledge-base-specific guidance for coder, debugger, and reviewer
- added semantic validation on generated artifacts

Validation rules added:

- preserve the first H1 as the note title
- reject known bad concept labels
- verify generated index links
- verify the note still captures the expected semantic relation

Outcome:

- the controller stopped accepting obviously weak outputs

## Phase 5: Provider Reliability and Fallback

Problems observed:

- Claude and Codex quota or CLI failures aborted runs too early
- errors looked like product bugs rather than provider availability problems

Fixes:

- generalized provider fallback in `llm.py`
- aggregate error reporting across providers
- separate planning/coding fallback order from debugging/review fallback order

Outcome:

- the system degrades more gracefully when one provider is unavailable

## Phase 6: Deterministic Execution Semantics

Problems observed:

- generated scripts using relative paths behaved differently depending on the current terminal working directory

Fixes:

- executor now runs code in the generated script's own isolated directory
- validator uses controlled local scratch directories instead of unstable system temp behavior

Outcome:

- knowledge-base tasks with `raw/`, `notes/`, and `state.json` behave much more predictably

## Phase 7: Doctor / Self-Check Mode

Problems observed:

- login problems, access-denied issues, and provider quota limits were hard to distinguish from code-generation issues

Fixes:

- added `--doctor`
- added `--doctor-live`
- added optional report export via `--doctor-output`
- added markdown/JSON output formats

What doctor checks:

- Python runtime
- scratch directory writability
- executor isolation behavior
- Claude/Codex path resolution
- API-key presence
- backend readiness
- optional live provider probes

Outcome:

- users can now diagnose environment failures before blaming the coding loop

## Phase 8: Documentation and Research Framing

Added:

- `docs/AGENT_SYSTEM_PAPER.md`
- `docs/PROJECT_UPDATE_LOG.md`

Purpose:

- turn the build process into a narrative suitable for portfolio, research-style writeup, and interview discussion

## Phase 9: Cross-Model Continuation

Problems observed:

- model quotas or token limits could interrupt a useful run
- switching from GPT-style workflows to Claude-style workflows usually meant losing local context
- long chat history was an inefficient handoff format

Fixes:

- added automatic session directories
- added compact `handoff.md` files
- saved `final_code.py` and `session.json` for every run
- exposed session output through the CLI

Outcome:

- a run can now be resumed by another model using a short handoff prompt and saved artifact path instead of replaying a long conversation

## Phase 10: Research Wiki Hardening

Problems observed:

- the first wiki ingester lived as a one-off generated script outside the main package
- concept extraction promoted low-value labels such as `Prompt`, `Docs`, `Source`, and `Success`
- source collection for paper writing and project code quality were drifting into separate workflows

Fixes:

- moved the wiki ingester into `src/agent_system/wiki_ingester.py`
- added conservative phrase-based concept extraction instead of broad single-word promotion
- filtered generic document labels more aggressively
- split note-title aliases from related concepts so knowledge-base notes stop linking to themselves
- added automated tests for concept quality and note generation
- documented a repeatable `python -m agent_system.wiki_ingester --root research_wiki` workflow

Outcome:

- the research wiki became part of the tracked, testable project surface
- note quality improved from "pipeline works" toward "notes are actually reusable"
- the same codebase now supports both project execution and source-base construction for writing

## Prompting Patterns That Worked Better

Better prompts had these traits:

- explicitly local-only
- explicit acceptance rules
- explicit forbidden outputs
- direct request for code only

Example pattern:

```text
Write a minimal local Python tool for [task].
Use only standard-library code unless absolutely necessary.
Preserve [specific invariant].
Do not emit [specific bad outputs].
Return only runnable Python code.
```

## Summary of Engineering Lessons

Main lesson:

- multiple agents do not create reliability by themselves

What actually improved the system:

- plan compression
- deterministic execution
- semantic validation
- provider fallback
- self-diagnostics

In short:

- the difficult part was not connecting Claude and Codex
- the difficult part was building a controller strict enough to manage them
