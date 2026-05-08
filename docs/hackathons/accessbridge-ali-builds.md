# AccessBridge CLI - ALI Builds Chicago

## Pitch

AccessBridge CLI helps under-resourced students make the most of authorized AI tool access by turning separate coding assistants into one cost-conscious learning workflow. Claude Code plans and implements, Codex debugs and reviews, and the system saves handoff artifacts so students do not waste limited monthly usage repeating context.

Subtitle:

```text
Subscription-aware AI coding workflow for under-resourced students.
```

## Problem

Many students do not struggle in computer science because they are not capable. They struggle because they debug alone.

A wealthier student can ask a tutor, a bootcamp mentor, a parent in tech, or a paid support network. A low-income or first-generation student may have one laptop, one authorized AI tool account, limited monthly usage, and no one to explain confusing errors.

## Solution

AccessBridge CLI turns existing AI coding access into a structured workflow:

1. Claude Code creates a short repair plan and first implementation.
2. A local Python executor runs the code and captures real errors.
3. Codex handles debugging, review, and second-opinion checks.
4. Student mode explains the result in beginner-friendly language.
5. Budget mode avoids unnecessary model calls and saves reusable artifacts.
6. `session.json`, `final_code.py`, and `handoff.md` preserve context for later.

The goal is not to replace learning. The goal is to give under-resourced students the kind of debugging support that wealthier students already get from tutors, mentors, and networks.

## Ethical Note

AccessBridge does not encourage account sharing or credential sharing. It is designed for students using their own accounts, school-provided access, free credits, or other authorized AI tool access.

## Demo Task

```text
A beginner student wrote a Python CSV todo app, but it crashes when loading saved tasks. Help explain the bug, fix the code, run it locally, and produce a short learning summary.
```

Run:

```powershell
python -m agent_system --student-mode --budget-mode --task "A beginner student wrote a Python CSV todo app, but it crashes when loading saved tasks. Help explain the bug, fix the code, run it locally, and produce a short learning summary."
```

Stable offline demo:

```powershell
$env:AGENT_DEMO_MODE="1"
python -m agent_system --student-mode --budget-mode --task "A beginner student wrote a Python CSV todo app, but it crashes when loading saved tasks. Help explain the bug, fix the code, run it locally, and produce a short learning summary." --session-dir .test_accessbridge_cli
```

## Demo Flow

1. Open with the student story: no tutor, confusing CSV bug, limited AI usage.
2. Run the AccessBridge CLI with `--student-mode --budget-mode`.
3. Show the guided stages:
   - planning
   - coding
   - executing
   - debugging only if needed
   - reviewing
   - done
4. Show the learning summary sections:
   - What was wrong
   - What was fixed
   - What you learned
5. Show `final_code.py` and `handoff.md`.
6. Explain that handoff prevents students from spending usage repeating context.

## Judging Criteria Mapping

Impact (30%):

- Helps low-income and first-generation students who lack tutors, mentors, or technical family networks.
- Reduces wasted usage from repeated manual prompting.
- Preserves context when students hit usage limits or need to continue later.

Creativity & Originality (25%):

- Reframes a multi-agent coding system as an equity tool.
- Turns separate AI coding assistants into a structured learning workflow.
- Uses handoff artifacts as a cost-conscious support mechanism.

Technical Effort (25%):

- Implements planner, coder, local executor, debugger, reviewer, session recorder, doctor mode, student mode, budget mode, and Web UI.
- Runs generated code locally and feeds real errors back into the workflow.
- Saves reusable `session.json`, `final_code.py`, and `handoff.md` artifacts.

Presentation & Communication (20%):

- Two-minute demo should focus on one beginner CSV bug.
- Slides should emphasize the hidden barrier: some students have debugging networks and others do not.
- Use plain language and avoid pitching account sharing.

## Two-Minute Video Script

```text
Many students do not fail computer science because they are not smart. They fail because they learn alone.

A wealthier student can ask a tutor, a bootcamp mentor, or a parent in tech. A low-income or first-generation student often has one laptop, one authorized AI tool account, and no one to explain confusing errors.

AccessBridge CLI helps close that gap.

Instead of asking students to know which AI tool to use, our CLI automatically routes the coding workflow. Claude Code handles planning and first-pass implementation. Codex handles debugging and review. A local executor runs the generated code, captures real errors, and sends only the necessary feedback into the next step.

This saves time and reduces wasted monthly usage. Students do not need to repeatedly explain the same problem to different tools. Every run saves final code, session history, and a handoff summary so they can continue later even if they hit a usage limit.

Here is a broken beginner Python project. AccessBridge creates a learning plan, writes the fix, runs the code, explains what changed, and produces a handoff summary.

The goal is not to replace learning. The goal is to give under-resourced students the kind of debugging support that wealthier students already get from tutors, mentors, and networks.
```

## Slide Outline

1. Title: AccessBridge CLI
2. Hidden barrier: debugging support is unevenly distributed
3. Target users: low-income and first-generation CS students
4. Product flow: Claude Code, local executor, Codex, handoff
5. Demo: beginner CSV todo bug
6. Impact: less repeated prompting, more learning continuity
7. Ethics: authorized access only, no account sharing

## Teammate Checklist

- You: run the CLI/UI demo twice and pick the smoothest flow for recording.
- Teammate 1: make 5-7 slides using this story and judging criteria.
- Teammate 2: record or edit the 2-minute video.
- Teammate 3 if available: polish the live pitch and prepare answers for ethics, cost, and whether this replaces learning.
- Everyone: verify the Devpost starter kit email and final submission fields before May 10, 2026.
