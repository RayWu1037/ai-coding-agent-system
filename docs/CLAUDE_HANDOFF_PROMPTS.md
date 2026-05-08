# Claude Handoff Prompts

This document collects reusable prompts for handing the `agent_system` project from one model or agent to Claude Code without replaying a long chat history.

For Codex CLI handoff prompts, see [`CODEX_HANDOFF_PROMPTS.md`](CODEX_HANDOFF_PROMPTS.md).

## How To Use

1. Make sure the latest run wrote a compact handoff file:
   `C:\Users\yixin\agent_system\.agent_system_sessions\latest\handoff.md`
2. Open Claude Code in:
   `C:\Users\yixin\agent_system`
3. Paste one of the prompts below.
4. Prefer the most specific prompt when you already know the next task.
5. Use the unified prompt when you want Claude to choose the highest-value next step.

## 1. Paper Continuation Prompt

```text
You are continuing an existing local AI engineering project.

Workspace:
C:\Users\yixin\agent_system

Read these files first:
1. C:\Users\yixin\agent_system\.agent_system_sessions\latest\handoff.md
2. C:\Users\yixin\agent_system\docs\UNDERGRAD_AI_WORKFLOW_PAPER.md
3. C:\Users\yixin\agent_system\docs\PAPER_SUBMISSION_PACKAGE.md
4. C:\Users\yixin\agent_system\docs\PROJECT_UPDATE_LOG.md
5. C:\Users\yixin\agent_system\README.md

Project context:
- This is a local multi-agent coding harness project already under active development.
- It supports Claude/Codex-style role separation, doctor mode, benchmarks, a research wiki ingester, and cross-model handoff.
- The repo has already been hardened significantly; do not restart from scratch.
- The latest git state already includes mid-run handoff checkpoints.

Primary goal for this turn:
1. Add author line, affiliation, email, and keywords to the main paper draft.
2. Create a UIC-forum-tailored short submission version based on the current paper.
3. Keep the repository internally consistent.

Important constraints:
- Make minimal, precise edits.
- Preserve the existing structure and wording when possible.
- Do not rewrite the full paper unless necessary.
- Prefer editing existing docs over creating redundant new ones.
- If you add a new doc for the UIC forum version, make it clearly named.
- If you change code, run local tests before finishing.
- If you only change docs, do a lightweight consistency check.

Expected outputs:
- Updated main paper draft
- A UIC-forum-targeted submission document
- Brief summary of what changed
- Note any remaining gaps before external submission

Use the handoff file as the compact authoritative state summary, and inspect the repo only as needed for implementation details.
```

## 2. Engineering Verification Prompt

```text
You are continuing an existing local AI engineering project.

Workspace:
C:\Users\yixin\agent_system

Read these files first:
1. C:\Users\yixin\agent_system\.agent_system_sessions\latest\handoff.md
2. C:\Users\yixin\agent_system\README.md
3. C:\Users\yixin\agent_system\docs\PROJECT_UPDATE_LOG.md
4. C:\Users\yixin\agent_system\src\agent_system\sessions.py
5. C:\Users\yixin\agent_system\src\agent_system\controller.py
6. C:\Users\yixin\agent_system\tests\test_sessions.py

Project context:
- This is a local multi-agent coding harness with Claude/Codex-style role separation.
- It already supports doctor mode, benchmarks, a research wiki ingester, and cross-model handoff.
- Mid-run checkpoint handoff was just added, so the next step is validation, not redesign.

Primary goal for this turn:
1. Validate that cross-model continuation really works from a mid-run checkpoint.
2. Simulate or execute a partial run that produces `current_code.py` and `handoff.md`.
3. Use the saved handoff context to continue the same task from the alternate backend or model path.
4. Document whether the continuation worked, what broke, and what should be improved next.

Important constraints:
- Do not rewrite the whole system.
- Prefer the smallest change that increases confidence in the handoff workflow.
- Preserve existing architecture and tests.
- Add or update tests if you find a real gap.
- Run local tests after code changes.
- If a real provider/quota/environment limitation blocks full verification, document that explicitly instead of faking success.

Expected outputs:
- A concrete verification result for mid-run cross-model continuation
- Any necessary code or test updates
- A short written note describing what was validated and what remains unverified

Use the handoff file as the authoritative compact state summary, and inspect the repository only when needed.
```

## 3. Outreach / Application Materials Prompt

```text
You are continuing an existing local AI engineering project and helping prepare external-facing application materials.

Workspace:
C:\Users\yixin\agent_system

Read these files first:
1. C:\Users\yixin\agent_system\.agent_system_sessions\latest\handoff.md
2. C:\Users\yixin\agent_system\docs\CANDIDATE_PROFILE.md
3. C:\Users\yixin\agent_system\docs\UNDERGRAD_AI_WORKFLOW_PAPER.md
4. C:\Users\yixin\agent_system\docs\PAPER_SUBMISSION_PACKAGE.md
5. C:\Users\yixin\agent_system\docs\SUBMISSION_MATERIALS.md
6. C:\Users\yixin\agent_system\docs\SUBMISSION_AND_OUTREACH_PLAN.md
7. C:\Users\yixin\agent_system\README.md

Project context:
- This repository is both a real software project and a portfolio/research artifact.
- The candidate is a systems-oriented undergraduate using this project to improve research, internship, and graduate-school opportunities.
- The repo already includes project documentation, research framing, a research wiki, and submission materials.
- Do not restart or duplicate existing work unnecessarily.

Primary goal for this turn:
1. Improve the external-facing project/application materials.
2. Tighten the writing so the project is legible to professors, recruiters, and undergraduate research reviewers.
3. Produce concise, high-signal materials that can actually be reused.

Priority outputs:
1. A polished short project description for resume / LinkedIn / outreach.
2. A professor outreach email draft tied to this project.
3. A concise research-interest blurb aligned with the paper and project.
4. If needed, small edits to existing docs so the materials stay consistent.

Important constraints:
- Keep everything in English only.
- Prefer concise, professional writing over hype.
- Do not invent achievements, results, or affiliations.
- Reuse the existing project framing where possible.
- Avoid redundant new files unless a clearly named artifact is worth adding.
- If you create new documents, make them directly reusable by the student.

Expected outputs:
- Reusable polished text artifacts
- Any doc updates needed for consistency
- A short summary of what should be used first for outreach

Use the handoff file as the compact state summary, and inspect the rest of the repository only as needed.
```

## 4. Hackathon Productization Prompt

```text
You are continuing an existing local AI engineering project and productizing it for three hackathon submissions.

Workspace:
C:\Users\yixin\agent_system

Read these files first:
1. C:\Users\yixin\agent_system\.agent_system_sessions\latest\handoff.md
2. C:\Users\yixin\agent_system\README.md
3. C:\Users\yixin\agent_system\docs\PROJECT_UPDATE_LOG.md
4. C:\Users\yixin\agent_system\docs\SUBMISSION_MATERIALS.md
5. C:\Users\yixin\agent_system\docs\SUBMISSION_AND_OUTREACH_PLAN.md
6. C:\Users\yixin\agent_system\docs\CANDIDATE_PROFILE.md

Project context:
- This repository is an existing multi-agent coding workspace with planner/coder/debugger/reviewer-style orchestration, doctor mode, benchmarks, sessions, and handoff continuity.
- The goal is not to create three unrelated codebases.
- The goal is to build one shared core product and package it as three focused sub-products for three different hackathons.
- Preserve the existing architecture and avoid restarting from scratch.
- Before final submission, verify all hackathon dates, rules, eligibility requirements, sponsor-track requirements, and submission materials on the official Devpost or organizer pages.

Primary product strategy:
1. Shared core:
   - Keep one reusable multi-agent execution engine.
   - Add or refine shared hackathon features only when they help at least two submissions:
     - Demo Mode
     - Run History
     - Handoff Viewer
     - Architecture Diagram
     - Stable demo task
     - Clean README / setup instructions
     - Public-facing license and repo hygiene
2. Google Cloud Rapid Agent Hackathon sub-product:
   - Product name: AgentRelay
   - Positioning: Resilient Multi-Agent Coding Workspace
   - Story: AgentRelay helps developers and students solve coding tasks through a transparent workflow: planner, coder, executor, debugger, reviewer, and recovery handoff.
   - Required direction: make the product clearly powered by Gemini or Google Cloud Agent Builder where feasible.
   - Sponsor-track fit: prioritize a GitLab/GitHub workflow or MongoDB run-memory workflow, depending on what is fastest and most credible in the repo.
   - Demo: issue or task -> plan -> code edit -> run/test -> debug loop -> review -> handoff summary.
3. ALI Builds Chicago sub-product:
   - Product name: AccessBridge
   - Positioning: AI Debugging Tutor for Students Without Coding Support
   - Story: some beginner programmers have tutors, experienced friends, and strong support networks; many do not. AccessBridge turns confusing programming errors into step-by-step learning help.
   - Social-impact framing: education equity, beginner support, lower barrier to debugging help.
   - UI/content vocabulary:
     - Plan -> Learning Plan
     - Review -> Explanation
     - Final Code -> Fixed Code
     - Timeline -> Debugging Steps
   - Demo: paste a broken beginner program -> explain the bug -> show fixed code -> explain what the student should learn next.
4. DevNetwork AI + ML Hackathon sub-product:
   - Product name: AgentRelay Resilience
   - Positioning: Resilient Agents with fallback, recovery, and handoff.
   - Story: what happens when an LLM provider fails, a tool times out, or generated code crashes? AgentRelay Resilience recovers through fallback providers, debugging loops, execution logs, and handoff summaries.
   - Track fit: TrueFoundry-style resilient agents or any sponsor challenge focused on reliable agent execution.
   - Demo: intentionally trigger a failure or flaky execution path -> show recovery -> show saved handoff and continuation.

Primary goal for this turn:
1. Inspect the current repository and identify the smallest practical set of changes needed to support the three-sub-product hackathon strategy.
2. Implement the highest-value shared foundation first.
3. Add or update hackathon-facing documentation so the three sub-products are clearly separated while sharing one technical core.
4. If time allows, create concrete submission packages for each sub-product.

Suggested branch strategy:
- Shared foundation branch: hackathon-agentrelay
- Education packaging branch: hackathon-accessbridge
- Resilience packaging branch: hackathon-resilience

Do not create branches automatically unless the user explicitly asks for branch creation in this turn. If branches already exist, work with the current branch and explain what should be split later.

Priority implementation order:
1. Repo hygiene:
   - Add or verify open-source license.
   - Clean README setup instructions and remove machine-specific private paths from public-facing docs.
   - Add a top-level Hackathon Submission section or a dedicated docs file.
2. Shared demo reliability:
   - Add Demo Mode or improve the existing demo path.
   - Add a stable demo task:
     "Fix this buggy Python CSV todo app, explain the bug, run the corrected code, and produce a handoff summary."
   - Make sure the demo does not depend on fragile paid-provider availability.
3. Product surfaces:
   - Add Run History page or docs if the UI already exists.
   - Add Handoff Viewer page or docs if the UI already exists.
   - Add an architecture diagram that explains planner/coder/debugger/reviewer/executor/handoff.
4. Submission packages:
   - docs/hackathons/agentrelay-google-cloud.md
   - docs/hackathons/accessbridge-ali-builds.md
   - docs/hackathons/agentrelay-resilience-devnetwork.md
   - Each file should include:
     - one-line pitch
     - problem
     - solution
     - target users
     - demo flow
     - technical architecture
     - judging-criteria mapping
     - remaining work checklist
5. Verification:
   - If code changes are made, run the relevant local tests.
   - If only docs are changed, do a consistency check across README and docs.

Important constraints:
- Keep the three sub-products clearly distinct in story, audience, and judging strategy.
- Keep the implementation shared unless a separation is truly necessary.
- Do not invent completed integrations. If Gemini, Google Cloud, GitLab, MongoDB, TrueFoundry, or other sponsor integrations are not actually implemented yet, label them as planned or next work.
- Prefer concrete demo flows over generic marketing language.
- Keep public-facing writing in English.
- Keep changes precise and avoid unrelated refactors.
- Preserve existing user work and do not delete existing docs unless clearly obsolete and confirmed.

Expected outputs:
- A completed shared foundation change, or a clear first-pass hackathon documentation package if code work is not yet appropriate.
- Three clearly named sub-product narratives:
  - AgentRelay for Google Cloud Rapid Agent Hackathon
  - AccessBridge for ALI Builds Chicago
  - AgentRelay Resilience for DevNetwork AI + ML Hackathon
- A concise summary of files changed.
- Tests or checks run.
- A short next-action list ordered by deadline and prize/fit.

Use the handoff file as the compact authoritative state summary, and inspect the repository only as needed for implementation details.
```

## 5. Unified Controller Prompt

```text
You are continuing an existing local AI engineering project.

Workspace:
C:\Users\yixin\agent_system

Read these files first:
1. C:\Users\yixin\agent_system\.agent_system_sessions\latest\handoff.md
2. C:\Users\yixin\agent_system\README.md
3. C:\Users\yixin\agent_system\docs\PROJECT_UPDATE_LOG.md
4. C:\Users\yixin\agent_system\docs\UNDERGRAD_AI_WORKFLOW_PAPER.md
5. C:\Users\yixin\agent_system\docs\PAPER_SUBMISSION_PACKAGE.md
6. C:\Users\yixin\agent_system\docs\CANDIDATE_PROFILE.md
7. C:\Users\yixin\agent_system\docs\SUBMISSION_AND_OUTREACH_PLAN.md

Project context:
- This repository is a local multi-agent coding harness plus a research/portfolio artifact.
- It already includes role-based orchestration, doctor mode, benchmarks, a research wiki ingester, paper drafts, and cross-model handoff support.
- The project has gone through many hardening iterations already.
- Do not restart from scratch or redesign without strong reason.

Your job:
1. Read the handoff and current repo state.
2. Identify the single highest-value next step.
3. Execute that step, not just analyze it.
4. Keep changes precise and consistent with the existing project direction.
5. If code changes are made, run appropriate tests.
6. If only docs/materials change, do a lightweight consistency pass.

Priority order for deciding the next step:
1. Fix any blocker that prevents reliable project use or handoff continuity.
2. Improve project quality if a small change materially increases reliability.
3. Improve the paper or submission materials if engineering is already stable.
4. Improve outreach/application artifacts if project and paper are in good shape.

Important constraints:
- Keep everything in English.
- Prefer small, high-leverage edits.
- Preserve the repo's current architecture and framing.
- Do not produce redundant documents if existing ones can be refined.
- If a task is blocked by quota/provider/environment issues, document that clearly and move to the next highest-value step.

Expected outputs:
- The chosen high-value change completed
- Any required code/doc updates
- Tests or checks run
- A short explanation of why that step was the best next move

Treat the handoff file as the compact authoritative status summary, and use the repository for implementation details.
```

## Practical Rule

Do not paste full chat history unless absolutely necessary.

Use:

- `handoff.md` for compact state
- `current_code.py` or `final_code.py` for the live artifact
- `docs/*.md` for stable project background

This keeps token cost lower and makes Claude continuation more reliable.
