# Paper Submission Package

## Title Options

1. **AI-Assisted Project Building for Systems-Oriented Undergraduates**
   A Case Study in Agentic Coding, Validation, and Cross-Model Continuation

2. **From Prompting to Orchestration**
   How a Computer Science Undergraduate Built and Hardened a Local AI Coding Harness

3. **Beyond One-Shot Code Generation**
   Failure Analysis and Workflow Design for Undergraduate AI-Assisted Software Projects

4. **Building with AI as an Undergraduate Engineer**
   A Case Study of Prompt Design, Semantic Validation, and Knowledge-Base Automation

## Preferred Abstract v2

This paper presents a case study of an undergraduate-built local AI coding harness and uses that build process to examine a broader question: what does effective AI-assisted software development actually require from a systems-oriented computer science student? The project combines planner, coder, debugger, reviewer, execution, validation, benchmarking, diagnostics, research-wiki ingestion, and cross-model handoff components into a single local workflow. Rather than treating large language models as one-shot generators, the study treats them as probabilistic collaborators inside a controlled engineering loop. The analysis identifies repeated failure classes, including environment faults misread as code faults, prompt overbreadth, semantic quality failure despite runnable output, and cross-model continuity loss under quota constraints. It then studies the interventions that improved reliability: planner compression, deterministic validators, provider fallback, local diagnostics, offline evaluation, tracked wiki-ingester heuristics, and compact handoff artifacts. The main conclusion is that AI meaningfully increases undergraduate leverage, but only when the student can specify constraints, recognize semantic failure, design acceptance checks, and preserve continuity across imperfect tools. This suggests that AI does not reduce the need for computer science fundamentals; instead, it raises the value of systems thinking, testing, debugging, and specification writing.

## 300-Word Forum Abstract

This project studies how a systems-oriented undergraduate can use AI to build a non-trivial software system while still preserving engineering rigor. The central artifact is a local multi-agent coding harness with role-based planning, coding, debugging, reviewing, execution, diagnostics, benchmarking, and session handoff support. The project also includes a research-wiki ingester that converts raw source notes into linked markdown notes, allowing the same system to support both implementation and writing.

The work began from a simple question: if large language models can already generate code, what still separates a fragile demo from a durable undergraduate project? The answer, based on repeated build-and-repair cycles, was that most failures did not come from syntax generation alone. Instead, the main problems were prompt overbreadth, environment instability, weak success criteria, relative-path assumptions, quota interruptions, and semantically incorrect outputs that still ran without crashing.

To address these problems, the project introduced several reliability layers: compressed planner output, task-specific validation, provider fallback, doctor-style environment checks, offline benchmarks, and compact handoff summaries that let one model continue work started by another. The knowledge-base ingester was later moved from a one-off generated script into tracked project code, making note quality heuristics testable and versioned.

The case study suggests that AI gives undergraduates real leverage, but only when paired with systems knowledge, debugging skill, specification discipline, and deterministic validation. In other words, AI changes how students build software, but it does not remove the need to think like engineers. The final result is both a working software project and a workflow argument for what computer science students should still learn in an AI-rich environment.

## Related Work Notes

### Agentic Coding Systems

- Use for framing the planner/coder/debugger/reviewer architecture.
- Tie to the argument that orchestration quality matters more than simply chaining models.

### Prompt Engineering Guidance

- Use official OpenAI and Anthropic guidance to support the claim that prompt quality behaves like specification quality.
- Connect to your findings on explicit constraints, output formatting, and iterative refinement.

### Personal Knowledge-Base Workflows

- Use the research-wiki component to position the project as more than a coding harness.
- Emphasize the loop from source ingestion to structured notes to paper writing.

### Undergraduate Engineering Education

- Frame the paper as a response to the claim that AI reduces the need for strong CS fundamentals.
- Position systems thinking, validation, and debugging as higher-value than raw syntax production.

## Reference Skeleton

Use a lightweight placeholder format first, then convert to the venue style later.

1. OpenAI. *Prompt Engineering Guide*. Official help article. Source in `research_wiki/raw/openai_prompt_engineering.md`.
2. Anthropic. *Prompt Engineering Overview*. Official documentation. Source in `research_wiki/raw/anthropic_prompt_engineering.md`.
3. Anthropic. *Claude Code Model Configuration*. Official documentation. Source in `research_wiki/raw/claude_code_model_config.md`.
4. Journal of Open Source Software. *Submission Requirements*. Source in `research_wiki/raw/joss_submission.md`.
5. University of Illinois Chicago. *Undergraduate Research Forum*. Source in `research_wiki/raw/uic_undergraduate_research_forum.md`.
6. This repository’s internal engineering record:
   - `docs/PROJECT_UPDATE_LOG.md`
   - `docs/AGENT_SYSTEM_PAPER.md`
   - `docs/PROMPTING_GUIDE.md`

## Next Conversion Steps

1. Pick one title and lock the abstract.
2. Convert the current bracketed references into the citation style required by the target venue.
3. Decide whether the Mermaid architecture diagram should stay inline or be redrawn as a figure image.
4. Refine Table 1 using venue-specific formatting rules.
5. Add author line, affiliation, and contact block to the main paper draft.

## Current Status

The main draft in `docs/UNDERGRAD_AI_WORKFLOW_PAPER.md` now includes:

- citation markers
- a system architecture figure
- a failure taxonomy table
- a references section
