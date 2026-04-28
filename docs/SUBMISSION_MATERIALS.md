# Submission Materials

## 1. Formal Paper Abstract

### Title

AI-Assisted Project Building for Systems-Oriented Undergraduates: A Case Study in Agentic Coding, Failure Analysis, Prompt Design, and Skill Prioritization

### Abstract

This paper examines how a systems-oriented undergraduate student can use large language models to design, implement, debug, document, and present a non-trivial software project. The case study is a local multi-agent coding harness built around planner, coder, debugger, reviewer, execution, validation, benchmark, and diagnostic components. Rather than treating AI as a one-shot code generator, the project treats AI as part of a longer engineering loop that includes constraint setting, runtime evaluation, artifact validation, and iterative repair. The study focuses on four questions: what failure modes repeatedly appear in AI-assisted project building, which prompt structures reduce those failures while conserving tokens, which engineering controls are necessary to convert runnable output into usable output, and which areas of computer science remain most valuable for undergraduates in an AI-rich workflow. The main findings are that many failures arise not from missing syntax but from weak orchestration, unclear success criteria, and environment ambiguity; that token-efficient prompts are usually narrow, constraint-heavy, and explicit about prohibited outputs; and that students still benefit strongly from learning systems thinking, software engineering discipline, data structures, debugging, and evaluation. The project suggests that AI raises undergraduate leverage most when the student acts as a rigorous orchestrator rather than a passive prompt user.

## 2. UIC Undergraduate Research Forum Abstract

### Title

From AI Coding Demo to Reliable Local Tooling: Building and Hardening a Multi-Agent Coding Harness

### Abstract

This project studies how a computer science undergraduate can use AI to build a non-trivial software system while still applying systems and software engineering principles. I developed a local multi-agent coding harness in Python that coordinates planner, coder, debugger, and reviewer roles, executes generated code locally, and validates the resulting artifacts. The project was inspired by modern AI coding workflows, but the main goal was not only to connect multiple models. Instead, the goal was to understand why AI-assisted project building often fails in practice and how those failures can be reduced.

During development, several recurring problems appeared: generated code could run successfully while still producing low-quality output, relative-path assumptions caused inconsistent behavior, model and CLI configuration issues looked like coding failures, and broad prompts wasted tokens while increasing instability. To address these problems, I added prompt constraints, plan compression, deterministic execution behavior, task-specific artifact validation, provider fallback, benchmark checks, and a doctor/self-check mode for environment diagnostics.

The result is a more reliable local coding harness that can be used both as a software artifact and as a case study in AI-assisted engineering. The broader conclusion is that AI is most useful to undergraduate students when combined with clear success criteria, validation loops, and strong systems reasoning. This work suggests that the future role of computer science students is not reduced by AI, but shifted toward specification, orchestration, debugging, and evaluation.

## 3. Project Promotion Copy

### LinkedIn / GitHub Project Blurb

I built a local multi-agent coding system that uses planner, coder, debugger, and reviewer roles to generate and repair Python projects through an execution-feedback loop. What made the project valuable was not just connecting Claude-style and Codex-style workflows, but hardening the system so it could handle real engineering failure modes: bad model defaults, Windows path issues, provider quotas, weak prompts, runnable-but-wrong outputs, and poor artifact quality.

The project now includes:

- dual CLI/API backends
- local execution and repair loops
- task-specific validation for generated artifacts
- doctor/self-check diagnostics
- offline benchmark/eval coverage
- a web UI for monitoring runs
- research-style documentation on prompt design, failure analysis, and AI-assisted undergraduate workflows

Repository:

- `https://github.com/RayWu1037/ai-coding-agent-system`

### Short GitHub README Highlight

This repository is a local multi-agent coding harness built to study what actually makes AI-assisted software work reliable. It includes role-based orchestration, execution-feedback loops, task-specific validation, provider fallback, diagnostics, offline benchmarks, and research-style documentation on how undergraduates can use AI to build real projects without giving up systems thinking and software engineering rigor.
