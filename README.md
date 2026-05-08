# AccessBridge CLI

[![CI](https://github.com/RayWu1037/ai-coding-agent-system/actions/workflows/ci.yml/badge.svg)](https://github.com/RayWu1037/ai-coding-agent-system/actions/workflows/ci.yml)

Subscription-aware AI coding workflow for under-resourced students.

AccessBridge CLI helps low-income and first-generation students get more value from the AI coding tools they already have by routing tasks between Claude Code for planning/implementation and Codex for debugging/review.

## Hackathon Focus: AccessBridge CLI

AccessBridge CLI is a subscription-aware AI coding workflow for under-resourced students.

Many low-income and first-generation students cannot afford private tutors, coding bootcamps, or multiple paid AI workflows. Even when they have access to monthly AI coding tools through personal subscriptions, school programs, or free credits, they often do not know how to use those tools efficiently.

AccessBridge CLI turns existing AI tool access into a structured workflow:

- Claude Code is used for planning and first-pass implementation.
- Codex is used for debugging, review, and second-opinion checks.
- The local executor runs generated code and captures real errors.
- Session and handoff files preserve progress so students do not waste usage limits repeating context.

The goal is not to replace learning. The goal is to make high-quality debugging support available to students who do not have mentors, tutors, or technical family networks.

AccessBridge does not encourage account sharing or credential sharing. It is designed for students using their own accounts, school-provided access, free credits, or other authorized AI tool access.

- Product: `AccessBridge CLI`
- ALI Builds demo: explain and fix a beginner Python CSV todo app, run it locally, and produce a learning summary
- Submission package: [`docs/hackathons/accessbridge-ali-builds.md`](docs/hackathons/accessbridge-ali-builds.md)
- Google Cloud materials are preserved separately at [`docs/hackathons/agentrelay-google-cloud.md`](docs/hackathons/agentrelay-google-cloud.md)

This project supports two runtime styles:

- `CLI backend`: use local Claude Code CLI for planning/coding and local Codex CLI for debugging/review
- `SDK backend`: use Gemini, Anthropic, and OpenAI API clients directly
- `Gemini backend`: require Gemini for all agent roles with `AGENT_BACKEND=gemini`
- `Student mode`: return beginner-friendly explanations with `AGENT_STUDENT_MODE=1` or `--student-mode`
- `Budget mode`: cap retries and save reusable artifacts with `AGENT_BUDGET_MODE=1` or `--budget-mode`
- `Demo mode`: use a deterministic offline AccessBridge demo with `AGENT_DEMO_MODE=1`

It also includes a local Web UI so the workflow can be demonstrated as a project instead of only a terminal script.

## Why This Project Matters

This repository is useful as an AI engineering portfolio project because it demonstrates:

- multi-agent orchestration instead of single-prompt scripting
- role-based decomposition with `Planner`, `Coder`, `Debugger`, and `Reviewer`
- tool-using agent loops that generate, execute, inspect, and revise code
- dual backend design that supports both API-driven and CLI-driven model access
- a runnable UI for demos, not just backend code

## Features

- controller loop that coordinates specialized agents
- local Python code execution with timeout and captured stdout/stderr
- Claude Code CLI plus Codex CLI integration
- Anthropic SDK plus OpenAI SDK integration
- Gemini API integration for the Google Cloud hackathon path
- environment-variable based configuration
- deterministic demo mode for stable judging walkthroughs
- student mode for beginner-friendly explanations
- budget mode for quota-saving workflows
- doctor/self-check mode for runtime, path, backend, and live provider diagnostics
- offline benchmark/eval suite for representative local workloads and artifact checks
- automatic session/handoff summaries for cross-model continuation
- tracked research-wiki ingester for turning source notes into linked markdown notes
- CLI entry point for single-task runs
- local Web UI for submitting tasks and inspecting runs

## Architecture

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
Final Code + Review Notes
```

Backend mapping:

- `Planner` and `Coder` prefer Claude in CLI mode
- `Debugger` and `Reviewer` prefer Codex in CLI mode
- SDK mode uses Anthropic for planning/coding and OpenAI for debugging/review

## Project Layout

```text
agent_system/
|- .env.example
|- .gitignore
|- pyproject.toml
|- README.md
|- requirements.txt
`- src/
   `- agent_system/
      |- __init__.py
      |- __main__.py
      |- config.py
      |- controller.py
      |- llm.py
      |- prompts.py
      |- wiki_ingester.py
      |- ui.py
      |- agents/
      |  |- __init__.py
      |  |- base.py
      |  |- coder.py
      |  |- debugger.py
      |  |- planner.py
      |  `- reviewer.py
      |- static/
      |  |- app.js
      |  |- index.html
      |  `- styles.css
      `- tools/
         |- __init__.py
         `- executor.py
```

## Requirements

- Windows with Python 3.10+
- either:
  - a valid `GEMINI_API_KEY` for the Google Cloud hackathon path
  - local `Claude Code` and `Codex` CLIs already authenticated
  - or valid `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`

## Installation

1. Create a local environment file:

```powershell
Copy-Item .env.example .env
```

2. Install dependencies:

```powershell
py -m pip install -r requirements.txt
py -m pip install -e .
```

## Configuration

The main switch is `AGENT_BACKEND`:

- `auto`: prefer local CLIs, fall back to SDKs
- `cli`: require local Claude Code CLI and Codex CLI
- `sdk`: require API keys

Important environment variables:

```env
AGENT_BACKEND=auto
AGENT_FAST_MODE=0
AGENT_STUDENT_MODE=0
AGENT_BUDGET_MODE=0
AGENT_DEMO_MODE=0
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=sonnet
GEMINI_MODEL=gemini-2.5-flash
CODEX_MODEL=
CLAUDE_CLI_PATH=
CODEX_CLI_PATH=
CLI_TIMEOUT_SECONDS=300
EXECUTION_TIMEOUT_SECONDS=8
MAX_DEBUG_ITERATIONS=3
```

## Running From The CLI

Basic usage:

```powershell
python -m agent_system --task "Build a command-line todo app with unit tests"
```

AccessBridge student + budget mode:

```powershell
python -m agent_system --student-mode --budget-mode --task "A beginner student wrote a Python CSV todo app, but it crashes when loading saved tasks. Help explain the bug, fix the code, run it locally, and produce a short learning summary."
```

Offline AccessBridge demo mode:

```powershell
$env:AGENT_DEMO_MODE="1"
python -m agent_system --student-mode --budget-mode --task "A beginner student wrote a Python CSV todo app, but it crashes when loading saved tasks. Help explain the bug, fix the code, run it locally, and produce a short learning summary."
```

Google Cloud / Gemini path:

```powershell
$env:AGENT_BACKEND="gemini"
$env:GEMINI_API_KEY="your-api-key"
python -m agent_system --task "Fix this buggy Python CSV todo app, explain the bug, run the corrected code, and produce a handoff summary."
```

GitLab issue demo path:

```powershell
$env:AGENT_DEMO_MODE="1"
python -m agent_system.gitlab_demo --issue docs\hackathons\samples\gitlab_issue_csv_todo.json --demo-mode --session-dir .agentrelay_gitlab_demo
```

This loads a GitLab-style issue payload, converts it into a guarded AgentRelay task, runs the agent workflow, and prints a GitLab comment draft that can later be posted through the GitLab MCP server.

One-click Windows wrapper:

```powershell
.\run_cli.bat "Build a command-line todo app with unit tests"
```

Fast mode for project-shaped tasks:

```powershell
python -m agent_system --fast --task "Write a minimal Python project for an Obsidian-style knowledge-base ingester"
```

Fast mode wrapper:

```powershell
.\run_cli.bat --fast "Write a minimal Python project for an Obsidian-style knowledge-base ingester"
```

Write the final generated code to a file:

```powershell
python -m agent_system --task "Write a stock backtester" --iterations 4 --output generated_backtester.py
```

Save session artifacts to a custom directory:

```powershell
python -m agent_system --task "Build a command-line todo app with unit tests" --session-dir sessions
```

Each run now saves:

- `session.json`
- `final_code.py`
- `handoff.md`

The handoff file is intentionally compact so you can switch from one model to another after quota or token exhaustion and continue from the saved local artifact.
Reusable Claude continuation prompts are collected in `docs/CLAUDE_HANDOFF_PROMPTS.md`.

Run static environment diagnostics:

```powershell
python -m agent_system --doctor
```

Run live provider diagnostics:

```powershell
python -m agent_system --doctor --doctor-live
```

Doctor wrapper examples:

```powershell
.\run_cli.bat --doctor
.\run_cli.bat --doctor --live
```

Save a doctor report to Markdown or JSON:

```powershell
.\run_cli.bat --doctor --output reports\doctor.md
.\run_cli.bat --doctor --live --output reports\doctor.json
```

Run offline benchmarks:

```powershell
.\run_cli.bat --benchmark
.\run_cli.bat --benchmark --benchmark-output reports\benchmarks.md
```

Build or refresh the local research wiki:

```powershell
python -m agent_system.wiki_ingester --root research_wiki
```

This ingests files from `research_wiki/raw/`, writes linked notes to `research_wiki/notes/`, and updates `research_wiki/state.json`.
Generated notes now keep short title variants under `aliases` and reserve `concepts` for related ideas, which helps reduce self-referential wiki noise.

## Running The Web UI

Start the local server:

```powershell
python -m agent_system.ui --port 8000
```

One-click Windows wrapper:

```powershell
.\run_ui.bat
```

Use a custom port:

```powershell
.\run_ui.bat 8080
```

Then open:

```text
http://127.0.0.1:8000
```

The UI shows:

- current job status
- per-stage timeline updates
- recent submitted jobs
- generated plan
- review notes
- final code output

## How The Loop Works

1. The controller receives a user task.
2. The planner turns the task into a short implementation plan.
3. The coder generates a full Python solution.
4. The executor runs that code locally and captures output.
5. If execution fails, the debugger revises the code.
6. The reviewer inspects the final version and returns concise notes.

## Example Demo Tasks

- `Build a command-line todo app with CSV persistence and unit tests`
- `Fix this buggy Python CSV todo app, explain the bug, run the corrected code, and produce a handoff summary.`
- `Write a Python script that analyzes a sales CSV and prints summary statistics`
- `Implement a simple backtesting engine with PnL and drawdown reporting`

## Backend Notes

### CLI Mode

Use this when you already have local model CLIs authenticated and want to avoid API key setup inside the project.

- Claude Code CLI is used for planning and initial code generation
- Codex CLI is used for debugging and review

### SDK Mode

Use this when you want predictable programmatic access through Python clients.

- Gemini can run all roles when `AGENT_BACKEND=gemini`
- Anthropic handles planning/coding by default
- OpenAI handles debugging/review by default

### Demo Mode

Use this when you need a stable offline walkthrough for judging, video recording, or UI rehearsal.

- set `AGENT_DEMO_MODE=1`
- submit the CSV todo demo task
- inspect the generated plan, timeline, final code, review, session artifacts, and handoff summary

## Troubleshooting

### Claude CLI says `Not logged in`

Open Claude Code CLI interactively and run login:

```powershell
C:\Users\yixin\.local\bin\claude.exe
```

Then complete `/login`.

### Codex CLI returns `Access is denied (os error 5)`

On this machine, `codex exec` worked when run outside the nested assistant sandbox, which suggests an environment restriction rather than a broken login.

Practical checks:

- verify `CODEX_CLI_PATH` points at the bundled `codex.exe`
- verify Codex login is complete
- retry from your own terminal instead of a nested sandboxed environment

### PowerShell blocks script shims

If `codex` or other npm-installed commands fail because of `.ps1` execution policy, call the underlying `.cmd` or `.exe` directly.

## Safety Notes

- generated code is executed locally
- only run trusted prompts
- generated code can be incorrect, incomplete, or unsafe
- this project is best treated as an experimentation and orchestration harness

## Resume-Friendly Summary

You can describe this project as:

> Built a local multi-agent coding system with planner/coder/debugger/reviewer roles, dual CLI/API backends, automated execution-feedback loops, and a browser-based monitoring UI.

## Future Extensions

- add persistent run history storage
- add automated test execution and test-result panels
- add Git integration for commit/branch/PR workflows
- add parallel sub-agents with separate workspaces
- add benchmark tasks and evaluation metrics
