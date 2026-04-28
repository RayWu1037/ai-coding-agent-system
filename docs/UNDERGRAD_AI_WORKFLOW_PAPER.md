# AI-Assisted Project Building for Systems-Oriented Undergraduates
## A Case Study in Agentic Coding, Failure Analysis, Prompt Design, and Skill Prioritization

### Abstract

This paper studies how a systems-oriented undergraduate can use large language models to design, implement, debug, document, and publicly present a non-trivial software project. The case study is a local multi-agent coding harness built around planner, coder, debugger, reviewer, execution, validation, benchmark, and diagnostic components. Instead of treating AI as a one-shot code generator, this work examines AI as a collaborator embedded in a longer engineering loop. The paper focuses on four questions: which failures repeatedly occur in AI-assisted project work, which prompt patterns reduce those failures while controlling token cost, which validation layers are necessary to turn runnable output into usable output, and which areas of computer science remain most valuable for undergraduates in an AI-rich workflow. The main result is that AI increases leverage, but only for students who can specify constraints, inspect failure modes, validate behavior, and restructure a system when naïve generation fails.

### 1. Introduction

A common claim in the current AI era is that students no longer need to know much programming because models can write code. This claim is overstated. In practice, AI improves speed most when the student can already reason about:

- system structure
- constraints
- failure modes
- correctness
- evaluation

This project provides a concrete case study. The target system was a local multi-agent coding harness inspired by real-world coding agents. The harness was built, stress-tested, repeatedly broken, and repeatedly hardened. The process exposed a wide gap between "AI can generate code" and "AI can reliably help build a durable project."

### 2. Research Questions

This paper is organized around four research questions:

1. What types of failures occur when an undergraduate uses AI to build a medium-complexity software project?
2. Which prompt strategies reduce these failures and conserve tokens?
3. What engineering controls are required to make AI-generated project work dependable?
4. In an AI-rich workflow, what should a computer science undergraduate still prioritize learning?

### 3. Case Study Project

The project under study is a local multi-agent coding system with the following components:

- planner
- coder
- debugger
- reviewer
- local Python executor
- task-specific validation
- benchmark/eval suite
- doctor/self-check diagnostics
- local Web UI

The system supports both:

- CLI backends using Claude Code CLI and Codex CLI
- SDK backends using Anthropic and OpenAI APIs

The project was developed iteratively under realistic constraints on Windows, including CLI quirks, path issues, quota limits, and environment variability.

### 4. Failure Taxonomy

The project exposed several recurring failure classes.

#### 4.1 Runnable but semantically wrong output

This was the most important failure pattern. The generated code might:

- execute successfully
- produce files
- still violate the user's real intent

For example, the knowledge-base ingester could use the wrong note title, extract noisy concepts, or generate malformed wiki links while still exiting successfully.

#### 4.2 Environment failures misread as coding failures

Many failures came from:

- model deprecations
- CLI login state
- shell permissions
- provider quotas
- output decoding differences

These failures initially looked like "the project is broken" when the real problem was environmental.

#### 4.3 Prompt overbreadth

Broad prompts such as "build the whole project" often caused:

- long plan output
- slower coding passes
- timeout risk
- heuristic overreach

Overly broad prompts increased both token cost and instability.

#### 4.4 Relative-path ambiguity

Generated scripts frequently assumed their own working directory. When the harness executed them from a different directory, behavior diverged from the intended tool design.

#### 4.5 Weak success criteria

A controller that treats `returncode == 0` as success is not strong enough for project-shaped tasks. That rule ignores many product-level errors.

### 5. What Reduced Failure

Several concrete design choices improved reliability.

#### 5.1 Narrower prompts with hard constraints

Better prompts:

- specified the runtime environment
- stated the acceptance rule
- prohibited known bad outputs
- asked for code only

Example pattern:

```text
Write a minimal local Python tool for [task].
Use only standard-library code unless absolutely necessary.
Preserve [specific invariant].
Do not emit [specific bad outputs].
Return only runnable Python code.
```

This reduced token waste by removing open-ended exploratory prose and focusing the model on implementation constraints.

#### 5.2 Planner compression

The planner was useful, but passing its entire output into the coder created bloat. Compacting plans before coding improved both speed and stability.

#### 5.3 Task-specific validation

The largest quality gain came from validation. Instead of asking the reviewer model to "notice" all errors, the system introduced explicit checks for:

- title fidelity
- malformed links
- low-value concept labels
- expected index structure

This turned vague dissatisfaction into deterministic rejection rules.

#### 5.4 Environment diagnostics

The addition of `doctor` and `doctor-live` split environment readiness from generation quality. This prevented wasted debugging effort and made provider problems legible.

#### 5.5 Benchmarks

Offline benchmark fixtures enabled repeatable evaluation even when model quotas were unavailable. This is especially important for student projects, where external service availability is not guaranteed.

#### 5.6 Cross-model handoff packaging

Another practical improvement was automatic session packaging. Each run now saves:

- a machine-readable session state
- the latest generated code artifact
- a compact handoff summary with the next recommended prompt

This matters because undergraduate users often work under quota or token limits. A compact handoff package makes it possible to continue the same task with another model without replaying the entire conversation history.

### 6. Prompting Principles for Lower Token Cost

Token efficiency improved when prompts obeyed five principles.

#### 6.1 Specify the implementation boundary

Bad:

```text
Build a full-featured app for ...
```

Better:

```text
Build the smallest runnable local implementation for ...
Prefer one Python file unless multiple files are strictly necessary.
```

#### 6.2 State what must not happen

Failure prevention prompts were often more effective than feature prompts. For example:

```text
Do not use API keys.
Do not emit malformed wiki links.
Do not replace the first H1 with a subsection heading.
```

#### 6.3 Request deterministic logic over cleverness

When parsing text, asking for "conservative, predictable logic" helped suppress brittle heuristic behavior.

#### 6.4 Ask for runnable code only

This reduced extra markdown, commentary, and formatting noise that complicates automated execution.

#### 6.5 Reuse local validation language

The most efficient repair prompts reused the exact words of validator failures. This reduced re-explanation and helped the debugger target the real issue.

### 7. What CS Students Still Need to Learn

AI changes the workflow, but it does not erase the value of core CS knowledge. This project suggests that undergraduates should prioritize the following areas.

#### 7.1 Systems thinking

Students still need to understand:

- processes
- filesystems
- working directories
- permissions
- environment variables
- I/O boundaries

Many project failures were systems failures, not language failures.

#### 7.2 Data structures and algorithms

Even with AI assistance, students must recognize whether generated solutions are structurally sensible and scalable.

#### 7.3 Software engineering discipline

Students should still learn:

- decomposition
- testing
- version control
- debugging
- documentation
- interface design

The highest-value work in the case study came from orchestration and validation, not from typing syntax.

#### 7.4 Numerical and probabilistic thinking

As AI systems become more stochastic, students benefit from understanding uncertainty, convergence, tradeoffs, and evaluation metrics.

#### 7.5 Prompt design as specification writing

Prompting should be taught less as "chat skill" and more as:

- requirement writing
- interface specification
- failure-boundary definition

This is closer to software engineering than to casual prompting.

### 8. Proposed Undergraduate AI Workflow

Based on this case study, a productive AI-assisted workflow for undergraduates looks like this:

1. Define the narrowest usable task.
2. State runtime and dependency constraints.
3. Generate a small plan.
4. Compress the plan before coding.
5. Generate code with hard failure constraints.
6. Execute locally.
7. Validate behavior with deterministic checks.
8. Use validator output as repair input.
9. Save a compact handoff summary for cross-model continuation.
10. Document the engineering process.
11. Convert the process into portfolio artifacts.

This workflow is substantially more effective than simply asking a model to "build the whole thing."

### 9. Implications

For students:

- AI is strongest when paired with systems judgment.

For educators:

- teaching should shift from syntax-only emphasis toward validation, decomposition, and evaluation.

For project building:

- the ability to design acceptance criteria may be more valuable than the ability to manually write every line of code.

### 10. Conclusion

The case study suggests a simple conclusion:

> AI raises the ceiling for undergraduates, but only if they can act as rigorous orchestrators rather than passive prompt users.

The students who benefit most from AI-assisted engineering will likely be those who can:

- specify constraints clearly
- reduce ambiguity
- detect semantic failure
- design validation loops
- understand systems behavior
- convert project work into public, reproducible artifacts

In that sense, AI does not eliminate the need for computer science fundamentals. It makes their practical value more obvious.
