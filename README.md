# Multi-Agent Coding System

A local multi-agent coding harness that mirrors a practical "controller + specialized agents + tool execution" workflow.

This project supports two runtime styles:

- `CLI backend`: use local Claude Code CLI for planning/coding and local Codex CLI for debugging/review
- `SDK backend`: use Anthropic and OpenAI API clients directly

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
- environment-variable based configuration
- doctor/self-check mode for runtime, path, backend, and live provider diagnostics
- offline benchmark/eval suite for representative local workloads and artifact checks
- automatic session/handoff summaries for cross-model continuation
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
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=sonnet
CODEX_MODEL=
CLAUDE_CLI_PATH=C:\Users\yixin\.local\bin\claude.exe
CODEX_CLI_PATH=C:\Users\yixin\AppData\Roaming\npm\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\codex\codex.exe
CLI_TIMEOUT_SECONDS=300
EXECUTION_TIMEOUT_SECONDS=8
MAX_DEBUG_ITERATIONS=3
```

## Running From The CLI

Basic usage:

```powershell
$env:PYTHONPATH="C:\Users\yixin\agent_system\src"
C:\Users\yixin\AppData\Local\Programs\Python\Python313\python.exe -m agent_system --task "Build a command-line todo app with unit tests"
```

One-click Windows wrapper:

```powershell
.\run_cli.bat "Build a command-line todo app with unit tests"
```

Fast mode for project-shaped tasks:

```powershell
$env:PYTHONPATH="C:\Users\yixin\agent_system\src"
C:\Users\yixin\AppData\Local\Programs\Python\Python313\python.exe -m agent_system --fast --task "Write a minimal Python project for an Obsidian-style knowledge-base ingester"
```

Fast mode wrapper:

```powershell
.\run_cli.bat --fast "Write a minimal Python project for an Obsidian-style knowledge-base ingester"
```

Write the final generated code to a file:

```powershell
$env:PYTHONPATH="C:\Users\yixin\agent_system\src"
C:\Users\yixin\AppData\Local\Programs\Python\Python313\python.exe -m agent_system --task "Write a stock backtester" --iterations 4 --output generated_backtester.py
```

Save session artifacts to a custom directory:

```powershell
$env:PYTHONPATH="C:\Users\yixin\agent_system\src"
C:\Users\yixin\AppData\Local\Programs\Python\Python313\python.exe -m agent_system --task "Build a command-line todo app with unit tests" --session-dir sessions
```

Each run now saves:

- `session.json`
- `final_code.py`
- `handoff.md`

The handoff file is intentionally compact so you can switch from one model to another after quota or token exhaustion and continue from the saved local artifact.

Run static environment diagnostics:

```powershell
$env:PYTHONPATH="C:\Users\yixin\agent_system\src"
C:\Users\yixin\AppData\Local\Programs\Python\Python313\python.exe -m agent_system --doctor
```

Run live provider diagnostics:

```powershell
$env:PYTHONPATH="C:\Users\yixin\agent_system\src"
C:\Users\yixin\AppData\Local\Programs\Python\Python313\python.exe -m agent_system --doctor --doctor-live
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
.\run_cli.bat --benchmark --output reports\benchmarks.md
```

## Running The Web UI

Start the local server:

```powershell
$env:PYTHONPATH="C:\Users\yixin\agent_system\src"
C:\Users\yixin\AppData\Local\Programs\Python\Python313\python.exe -m agent_system.ui --port 8000
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
- `Write a Python script that analyzes a sales CSV and prints summary statistics`
- `Implement a simple backtesting engine with PnL and drawdown reporting`

## Backend Notes

### CLI Mode

Use this when you already have local model CLIs authenticated and want to avoid API key setup inside the project.

- Claude Code CLI is used for planning and initial code generation
- Codex CLI is used for debugging and review

### SDK Mode

Use this when you want predictable programmatic access through Python clients.

- Anthropic handles planning/coding by default
- OpenAI handles debugging/review by default

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
