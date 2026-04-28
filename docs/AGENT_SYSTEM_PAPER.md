# Toward a Practical Multi-Agent Coding Harness on Windows:
## From CLI Demo to More Reliable Local Orchestration

### Abstract

This project started as a local recreation of a "Claude + Codex" style coding-agent stack: one model plans and writes code, another model debugs and reviews it, and a controller executes code between model calls. The initial version was runnable, but it was not stable enough for project-shaped tasks. This paper summarizes how the system was hardened from a narrow demo into a more reliable local harness. The main contribution is not the use of multiple LLMs by itself, but the introduction of execution discipline, deterministic validation, provider fallback, and environment diagnostics. We show that quality failures in multi-agent coding systems are often orchestration failures rather than model failures.

### 1. Introduction

The common public framing of coding agents is deceptively simple:

```text
Claude writes code -> Codex fixes code -> task completes
```

In practice, this is incomplete. A usable coding harness requires:

- prompt discipline
- execution feedback
- deterministic acceptance criteria
- backend fallback
- environment diagnostics

Without these layers, a system can produce code that is executable but not usable, or can fail because of provider quotas, CLI permissions, or path/layout mismatches that have nothing to do with the user's task.

### 2. System Architecture

The current system uses the following structure:

```text
User Task
  ->
Controller
  ->
Planner
  ->
Coder
  ->
Python Executor
  ->
Debugger
  ->
Reviewer
  ->
Validation + Final Output
```

The implementation supports two backend modes:

- CLI mode: `Claude Code CLI` for planning/coding and `Codex CLI` for debugging/review
- SDK mode: Anthropic for planning/coding and OpenAI for debugging/review

### 3. Main Engineering Problems Encountered

#### 3.1 Model output was runnable but semantically weak

The first major failure pattern was not syntax or runtime failure. It was semantic drift. A generated knowledge-base ingester could:

- run successfully
- create files
- still produce the wrong title
- still extract noisy concepts
- still generate low-value or malformed wiki links

The important lesson is that `exit code 0` is not an adequate notion of success for many AI-generated tools.

#### 3.2 Relative paths broke evaluation

Generated scripts often used relative paths such as `raw/`, `vault/`, `notes/`, and `state.json`. Early versions executed generated code without guaranteeing that the runtime working directory matched the generated file's directory. This caused false negatives and false positives during testing.

#### 3.3 Provider failures looked like product bugs

Several errors came from the environment rather than the code:

- deprecated Anthropic model names
- Windows execution policy issues
- Codex CLI access-denied behavior inside restricted shells
- daily usage or quota limits on Claude and Codex

Without proper classification, these failures looked like "the CLI is broken" even when the controller logic was fine.

#### 3.4 The controller was initially too trusting

Early versions of the controller:

- accepted execution success without semantic validation
- lacked robust provider fallback
- allowed reviewer-induced rewrites to bypass the same validation rules
- pushed large planner output directly into the coder

This made the system brittle for medium-complexity tasks.

### 4. Hardening Steps

#### 4.1 Prompt and task-profile constraints

The first stabilization step was to stop relying on generic prompts. The system now uses task-specific guidance for knowledge-base style tasks. The guidance explicitly requires:

- preserving the first top-level H1 as the note title
- rejecting generic labels such as `Core Idea`, `Notes`, and `Summary`
- avoiding malformed `[[links]]`
- preferring local-only implementations over API-key-based shortcuts

This was implemented through `task_profiles.py` so the logic is reusable across coder, debugger, and reviewer roles.

#### 4.2 Plan compression and fast mode

Long planner output made coder runs slower and less stable. The controller now:

- compacts plans before passing them to the coder
- supports a `--fast` mode
- retries with a smaller fallback plan if the initial coding step times out

This reduced the planner-to-coder context burden for project-shaped tasks.

#### 4.3 Deterministic semantic validation

The most important quality improvement was adding artifact validation. For knowledge-base tasks, the controller now validates generated artifacts by running the produced script in a small controlled environment and inspecting whether:

- the main note title matches the expected source H1
- low-value concepts such as `Notes. Concept` are absent
- the index links to the right note
- the note preserves the core semantic relation expected by the task

This changed the system from "generated code plus hope" into "generated code plus acceptance test."

#### 4.4 Provider fallback and aggregated failure reporting

The provider layer now tries multiple backends in sequence instead of aborting on the first failure. Failures are aggregated so the user can see which providers failed and why. This makes the system behave more like a production orchestrator and less like a thin wrapper around a single CLI.

#### 4.5 Deterministic execution directories

The executor now runs generated code in the generated script's own isolated directory. This fixed a large class of path-dependent bugs and made local evaluation align with the generated tool's own assumptions.

#### 4.6 Doctor/self-check mode

To separate environment issues from code-generation issues, a `doctor` mode was added. It provides:

- static checks for runtime, path resolution, scratch write access, executor behavior, and backend readiness
- optional live probes for Claude and Codex
- markdown or JSON report output for troubleshooting and archival

This is crucial for local AI tooling, where a quota problem or login problem can otherwise be mistaken for a model-quality problem.

### 5. Prompting Strategy That Worked Better

The most effective prompt pattern was not "write the full project." It was a narrower, constraint-heavy style:

```text
Write a minimal Python project for an Obsidian-style knowledge-base ingester.
It should process files from a raw folder, track processed files, and generate wiki markdown notes with [[links]] for concepts and summaries.
Prefer a local-only implementation.
Preserve the first H1 as the note title.
Reject generic concepts such as Core Idea, Notes, and Summary.
Return only runnable Python code.
```

More generally, web or tool-building prompts worked better when they specified:

- what must be local vs hosted
- what counts as success
- what forms of output are unacceptable
- whether one-file or multi-file output is preferred

For coding-agent workflows, the following prompt pattern is recommended:

1. State the task in one sentence.
2. State the runtime constraint.
   Example: "Use only local files and standard-library code."
3. State the acceptance rule.
   Example: "Preserve the first H1 as the note title."
4. State the prohibited failure modes.
   Example: "Do not emit malformed wiki links or generic placeholder concepts."
5. Ask for code only.

### 6. What the Dialogue Revealed

The interaction history revealed a consistent pattern:

- the user pushed from demo-level expectations toward production-level reliability
- the weak point was not "multi-agent" as a concept
- the weak point was orchestration quality

The practical lesson is that users often interpret model errors, environment failures, and orchestration mistakes as one problem. A useful system must separate them. That is why `doctor`, validation, fallback, and execution discipline mattered more than merely adding another model backend.

### 7. Remaining Gaps

The system is significantly more stable than its initial form, but it is still not a full industrial platform. Remaining work includes:

- persistent run history
- benchmark suites across task categories
- richer static validators for more project types
- provider health caching and cooldown logic
- explicit retry policy tuning by failure class
- Git-integrated review loops

### 8. Conclusion

The main conclusion is straightforward:

> Multi-agent coding systems do not become reliable just by chaining models together.

They become more reliable when the controller enforces:

- constrained generation
- deterministic execution
- artifact validation
- provider fallback
- environment diagnosis

That is the difference between a coding-agent demo and a practical local harness.
