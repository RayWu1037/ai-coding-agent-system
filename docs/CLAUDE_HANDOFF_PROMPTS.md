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

## 4. Unified Controller Prompt

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
