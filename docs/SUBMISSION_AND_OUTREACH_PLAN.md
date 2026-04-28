# Submission and Outreach Plan

## Objective

Use the `ai-coding-agent-system` project as a visibility asset for:

- internships
- undergraduate research opportunities
- future graduate-school applications
- public technical credibility

This plan is intentionally realistic. It separates:

- channels that are high-probability right now
- channels that become realistic after more hardening
- channels that are currently low-probability and should not be the first priority

## Current Project Status

Strengths:

- public GitHub repository
- strong AI-engineering narrative
- multi-agent orchestration angle
- diagnostics, validation, benchmarks, and UI already present
- supporting documentation and paper draft already exist

Current limitations:

- repository is still very new
- no external users or citations yet
- no comparative benchmark study against external baselines yet
- not yet a mature open-source project with six-plus months of public history

## Best Immediate Options

### 1. GitHub + LinkedIn + technical article rollout

Why:

- fastest path to visibility
- directly useful for internship and admissions review
- fully under your control

Recommended package:

- polished GitHub repo
- pinned repository on GitHub profile
- LinkedIn post explaining:
  - what the system does
  - what problems you hit
  - what engineering choices made it more reliable
- one technical article based on `docs/AGENT_SYSTEM_PAPER.md`

Suggested article titles:

- `What It Actually Takes to Make a Local Coding Agent Reliable`
- `From Claude + Codex Demo to a More Reliable Multi-Agent Coding Harness`
- `Why Multi-Agent Coding Systems Fail Without Validation and Diagnostics`

### 2. Devpost / project showcase submissions

Why:

- easier acceptance path than journals
- better fit for an engineering portfolio project
- good public artifact format

What to prepare:

- project thumbnail
- short demo GIF or screen recording
- concise story:
  - problem
  - architecture
  - failures encountered
  - hardening steps
  - benchmark/doctor results

### 3. UIC undergraduate research and poster-style presentation

Why:

- very credible for an undergraduate profile
- more realistic than journal publication right now
- aligns with your current academic stage

Best framing:

- not just "I built a coding tool"
- instead:
  - evaluation of reliability constraints in local multi-agent coding systems
  - comparison between naive orchestration and validated orchestration

## Medium-Term Options

### 4. JOSS (Journal of Open Source Software)

This is the most plausible journal-style target for this project, but not immediately.

Why it fits:

- software-focused
- short paper format
- open-source software is the core submission object

Why it is probably too early today:

- JOSS requires sustained public open development history
- JOSS expects a feature-complete package with tests and documentation
- JOSS expects clear research relevance and evidence of real use

Before JOSS becomes realistic, the project should add:

- an explicit OSI-approved license
- releases/tags
- CI
- more documented benchmark results
- stronger packaging polish
- at least several months of public history

### 5. arXiv preprint

Possible later, but not the first move.

What would make it stronger:

- a more formal evaluation study
- comparisons against baselines
- clearer methodology and results section
- a better-defined research question than "I built a useful project"

## Low-Priority / Low-Probability Right Now

### Traditional peer-reviewed AI/CS journals

For your current stage and this project state, these are not the highest-probability route.

Reason:

- the project is currently strongest as engineering software, not as a completed research study with novel scientific results
- journal review cycles are slow
- the acceptance bar is much higher than what is needed for admissions or internship visibility

## Recommended Execution Order

### Stage A: Immediate

1. Keep the repository updated with the latest hardening work.
2. Add screenshots or short demo media.
3. Publish a short LinkedIn launch post.
4. Publish one longer technical article based on the existing paper draft.

### Stage B: Next 1 to 2 months

1. Add CI and releases.
2. Expand benchmark coverage.
3. Add one comparative experiment section to the paper.
4. Package the repository more cleanly as reusable software.

### Stage C: After more public history

1. Reassess JOSS readiness.
2. Rework the paper into a software submission format if the repository has matured enough.

## Suggested Materials To Produce Next

- `project one-liner`
- `resume bullet`
- `LinkedIn launch post`
- `Medium/dev.to article draft`
- `UIC abstract draft`
- `JOSS readiness checklist`

## Information Still Needed From You

To make the next round of outreach materials accurate, I still need:

- whether you want to optimize mainly for:
  - internships
  - research assistant positions
  - graduate admissions
  - all three
- whether you already work with any UIC faculty member who could sponsor a forum/research submission
- whether you want outreach material in:
  - English only
  - English + Chinese
- whether you want me to produce:
  - a polished LinkedIn post
  - resume bullets
  - a one-page project abstract
  - a JOSS readiness checklist

## References

- JOSS submission guidance: https://joss.readthedocs.io/en/latest/submitting.html
- JOSS review criteria: https://joss.readthedocs.io/en/latest/review_criteria.html
- UIC Undergraduate Research Forum: https://undergradresearch.uic.edu/urf/
- UIC Undergraduate Research Hub: https://undergradresearch.uic.edu/
- Devpost submission guide: https://help.devpost.team/article/249-how-to-submit-your-project
