from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from agent_system.agents.coder import CoderAgent
from agent_system.benchmarks import run_benchmarks
from agent_system.agents.debugger import DebuggerAgent
from agent_system.agents.planner import PlannerAgent
from agent_system.agents.reviewer import ReviewerAgent
from agent_system.config import load_settings
from agent_system.doctor import run_doctor
from agent_system.llm import LLMError, LLMRegistry
from agent_system.sessions import SessionRecorder
from agent_system.task_profiles import is_knowledge_base_task
from agent_system.tools.executor import PythonExecutor
from agent_system.validation import (
    inspect_knowledge_base_artifacts,
    knowledge_base_validation_sample,
)


@dataclass
class RunSummary:
    plan: str
    final_code: str
    review: str
    iterations_used: int
    success: bool
    last_stdout: str = ""
    last_stderr: str = ""
    failure_stage: str = ""


StatusCallback = Callable[[str, str], None]


AGENTRELAY_DEMO_CODE = '''\
from __future__ import annotations

import argparse
import csv
from pathlib import Path


FIELDNAMES = ["id", "title", "done"]


def load_todos(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            {"id": row["id"], "title": row["title"], "done": row.get("done", "0")}
            for row in reader
            if row.get("id") and row.get("title")
        ]


def save_todos(path: Path, todos: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(todos)


def next_id(todos: list[dict[str, str]]) -> str:
    if not todos:
        return "1"
    return str(max(int(todo["id"]) for todo in todos) + 1)


def add_todo(path: Path, title: str) -> None:
    todos = load_todos(path)
    todos.append({"id": next_id(todos), "title": title, "done": "0"})
    save_todos(path, todos)
    print(f"Added: {title}")


def list_todos(path: Path) -> None:
    for todo in load_todos(path):
        status = "done" if todo["done"] == "1" else "open"
        print(f"{todo['id']}. {todo['title']} [{status}]")


def complete_todo(path: Path, todo_id: str) -> None:
    todos = load_todos(path)
    for todo in todos:
        if todo["id"] == todo_id:
            todo["done"] = "1"
            save_todos(path, todos)
            print(f"Completed: {todo['title']}")
            return
    raise SystemExit(f"No todo with id {todo_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CSV-backed todo app")
    parser.add_argument("--file", default="todos.csv")
    subcommands = parser.add_subparsers(dest="command", required=True)
    add = subcommands.add_parser("add")
    add.add_argument("title")
    subcommands.add_parser("list")
    done = subcommands.add_parser("done")
    done.add_argument("id")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    path = Path(args.file)
    if args.command == "add":
        add_todo(path, args.title)
    elif args.command == "list":
        list_todos(path)
    elif args.command == "done":
        complete_todo(path, args.id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


class Controller:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.executor = PythonExecutor(
            timeout_seconds=self.settings.execution_timeout_seconds
        )
        if self.settings.demo_mode:
            return
        self.llms = LLMRegistry(self.settings)
        self.planner = PlannerAgent(self.llms)
        self.coder = CoderAgent(self.llms)
        self.debugger = DebuggerAgent(self.llms)
        self.reviewer = ReviewerAgent(self.llms)

    def run(
        self,
        task: str,
        iterations: int | None = None,
        fast_mode: bool | None = None,
        student_mode: bool | None = None,
        budget_mode: bool | None = None,
        on_status: StatusCallback | None = None,
        recorder: SessionRecorder | None = None,
    ) -> RunSummary:
        use_student_mode = self.settings.student_mode if student_mode is None else student_mode
        use_budget_mode = self.settings.budget_mode if budget_mode is None else budget_mode
        if self.settings.demo_mode:
            return self._run_demo(
                task,
                student_mode=use_student_mode,
                budget_mode=use_budget_mode,
                on_status=on_status,
                recorder=recorder,
            )

        use_fast_mode = (self.settings.fast_mode if fast_mode is None else fast_mode) or use_budget_mode
        max_iterations = iterations or self.settings.max_debug_iterations
        if use_budget_mode:
            max_iterations = min(max_iterations, 1)
        review_repair_budget = 0 if use_budget_mode else (2 if not use_fast_mode else 1)
        self._notify(on_status, "planning", "Building implementation plan.")
        plan = self.planner.run(
            task,
            student_mode=use_student_mode,
            budget_mode=use_budget_mode,
        ).content
        compact_plan = self._compact_plan(plan, fast_mode=use_fast_mode)
        if recorder is not None:
            recorder.checkpoint(plan=compact_plan, iterations_used=0)
        self._notify(on_status, "coding", "Generating initial solution.")
        try:
            code = self.coder.run(task, compact_plan).content
        except TimeoutError:
            self._notify(
                on_status,
                "coding",
                "Initial code generation timed out; retrying with a shorter plan.",
            )
            code = self.coder.run(
                task,
                self._fallback_plan(task, compact_plan, fast_mode=use_fast_mode),
            ).content
        if recorder is not None:
            recorder.checkpoint(
                plan=compact_plan,
                code=code,
                iterations_used=0,
                failure_stage="coding",
            )
        success = False
        iterations_used = 0
        last_stdout = ""
        last_stderr = ""
        failure_stage = ""

        for index in range(max_iterations + 1):
            iterations_used = index + 1
            self._notify(
                on_status,
                "executing",
                f"Running generated code (attempt {iterations_used}/{max_iterations + 1}).",
            )
            result = self.executor.run(code)
            last_stdout = result.stdout
            last_stderr = result.stderr
            failure_stage = "executing"
            if result.succeeded:
                validation_feedback = self._validate_successful_output(task, code)
                if validation_feedback:
                    result.stderr = validation_feedback
                    result.returncode = 2
                    last_stderr = validation_feedback
                    failure_stage = "validation"
            if result.succeeded:
                success = True
                failure_stage = ""
                self._notify(
                    on_status,
                    "success",
                    f"Execution succeeded on attempt {iterations_used}.",
                )
                if recorder is not None:
                    recorder.checkpoint(
                        plan=compact_plan,
                        code=code,
                        success=True,
                        iterations_used=iterations_used,
                        failure_stage="",
                        last_stdout=last_stdout,
                        last_stderr=last_stderr,
                    )
                break
            if recorder is not None:
                recorder.checkpoint(
                    plan=compact_plan,
                    code=code,
                    success=False,
                    iterations_used=iterations_used,
                    failure_stage=failure_stage,
                    last_stdout=last_stdout,
                    last_stderr=last_stderr,
                )
            if index == max_iterations:
                break
            self._notify(
                on_status,
                "debugging",
                f"Execution failed on attempt {iterations_used}; requesting fix.",
            )
            code = self.debugger.run(task, code, result.stdout, result.stderr).content
            if recorder is not None:
                recorder.checkpoint(
                    plan=compact_plan,
                    code=code,
                    success=False,
                    iterations_used=iterations_used,
                    failure_stage="debugging",
                    last_stdout=last_stdout,
                    last_stderr=last_stderr,
                )

        self._notify(on_status, "reviewing", "Reviewing final code.")
        review = self.reviewer.run(
            task,
            code,
            student_mode=use_student_mode,
            budget_mode=use_budget_mode,
        ).content
        if recorder is not None:
            recorder.checkpoint(
                plan=compact_plan,
                code=code,
                review=review,
                success=success,
                iterations_used=iterations_used,
                failure_stage=failure_stage,
                last_stdout=last_stdout,
                last_stderr=last_stderr,
            )
        while (
            success
            and review_repair_budget > 0
            and self._review_suggests_changes(review)
        ):
            self._notify(
                on_status,
                "debugging",
                "Reviewer found issues; applying one improvement pass.",
            )
            code = self.debugger.run(
                task,
                code,
                "[execution previously succeeded]",
                "",
                review_feedback=review,
            ).content
            self._notify(on_status, "executing", "Re-running improved code after review.")
            rerun = self.executor.run(code)
            if rerun.succeeded:
                validation_feedback = self._validate_successful_output(task, code)
                if validation_feedback:
                    rerun.stderr = validation_feedback
                    rerun.returncode = 2
            last_stdout = rerun.stdout
            last_stderr = rerun.stderr
            failure_stage = "" if rerun.succeeded else "review_repair"
            iterations_used += 1
            success = rerun.succeeded
            review_repair_budget -= 1
            if recorder is not None:
                recorder.checkpoint(
                    plan=compact_plan,
                    code=code,
                    success=success,
                    iterations_used=iterations_used,
                    failure_stage=failure_stage,
                    last_stdout=last_stdout,
                    last_stderr=last_stderr,
                )
            self._notify(on_status, "reviewing", "Reviewing improved code.")
            review = self.reviewer.run(
                task,
                code,
                student_mode=use_student_mode,
                budget_mode=use_budget_mode,
            ).content
            if recorder is not None:
                recorder.checkpoint(
                    plan=compact_plan,
                    code=code,
                    review=review,
                    success=success,
                    iterations_used=iterations_used,
                    failure_stage=failure_stage,
                    last_stdout=last_stdout,
                    last_stderr=last_stderr,
                )
        self._notify(on_status, "done", "Run complete.")
        return RunSummary(
            plan=compact_plan,
            final_code=code,
            review=review,
            iterations_used=iterations_used,
            success=success,
            last_stdout=last_stdout,
            last_stderr=last_stderr,
            failure_stage=failure_stage,
        )

    @staticmethod
    def _notify(callback: StatusCallback | None, stage: str, message: str) -> None:
        if callback is not None:
            callback(stage, message)

    def _run_demo(
        self,
        task: str,
        student_mode: bool = False,
        budget_mode: bool = False,
        on_status: StatusCallback | None = None,
        recorder: SessionRecorder | None = None,
    ) -> RunSummary:
        if student_mode or budget_mode:
            plan = "\n".join(
                [
                    "1. Identify why the saved CSV todo file crashes for a beginner user.",
                    "2. Fix file loading with safe existence checks and csv.DictReader.",
                    "3. Keep the CLI small so the student can read and rerun it.",
                    "4. Run the fixed code locally and keep only useful error evidence.",
                    "5. Save final_code.py and handoff.md so no context is wasted.",
                ]
            )
        else:
            plan = "\n".join(
                [
                    "1. Reproduce the CSV todo bug with a tiny sample file.",
                    "2. Replace fragile row parsing with csv.DictReader and csv.DictWriter.",
                    "3. Keep the command-line interface small: add, list, done, and report.",
                    "4. Execute the fixed program locally and capture stdout/stderr.",
                    "5. Review edge cases and write a compact handoff summary.",
                ]
            )
        code = AGENTRELAY_DEMO_CODE
        if student_mode or budget_mode:
            review = "\n".join(
                [
                    "What was wrong",
                    "The app treated the saved CSV file as if it was always present and always well-formed. That is risky for beginner projects because the first run may not have a file yet, and saved rows can contain commas or missing values.",
                    "",
                    "What was fixed",
                    "The fixed version checks whether the file exists, uses Python's csv.DictReader and csv.DictWriter instead of manual splitting, and keeps add/list/done commands small enough to inspect.",
                    "",
                    "What you learned",
                    "Local persistence needs defensive loading: check for missing files, parse structured data with the right library, and save a handoff so you can continue later without re-explaining the bug or spending extra AI usage.",
                ]
            )
        else:
            review = "\n".join(
                [
                    "No issues found.",
                    "Demo notes: the fixed implementation uses the Python standard library, validates CSV rows, and keeps all file writes behind a single helper so the workflow is easy to inspect.",
                    "Google Cloud path: run this same task with AGENT_BACKEND=gemini and GEMINI_API_KEY set to let Gemini drive planning, coding, debugging, and review while AgentRelay records the execution timeline and handoff.",
                    "Partner MCP path: connect a GitLab MCP server so the task can start from an issue and end with a reviewable patch plus session artifacts.",
                ]
            )
        label = "AccessBridge" if student_mode or budget_mode else "AgentRelay"
        self._notify(on_status, "planning", f"Demo mode: loaded {label} CSV todo learning plan.")
        if recorder is not None:
            recorder.checkpoint(plan=plan, iterations_used=0)
        self._notify(on_status, "coding", "Demo mode: produced the corrected Python implementation.")
        if recorder is not None:
            recorder.checkpoint(
                plan=plan,
                code=code,
                iterations_used=0,
                failure_stage="coding",
            )
        self._notify(on_status, "executing", "Demo mode: simulated a successful local execution.")
        stdout = "Added: write proposal\nAdded: record demo\n1. write proposal [open]\n2. record demo [open]\n"
        if recorder is not None:
            recorder.checkpoint(
                plan=plan,
                code=code,
                success=True,
                iterations_used=1,
                last_stdout=stdout,
                last_stderr="",
            )
        self._notify(on_status, "reviewing", "Demo mode: generated beginner-friendly explanation and handoff notes.")
        if recorder is not None:
            recorder.checkpoint(
                plan=plan,
                code=code,
                review=review,
                success=True,
                iterations_used=1,
                last_stdout=stdout,
                last_stderr="",
            )
        self._notify(on_status, "done", "Demo run complete.")
        return RunSummary(
            plan=plan,
            final_code=code,
            review=review,
            iterations_used=1,
            success=True,
            last_stdout=stdout,
            last_stderr="",
            failure_stage="",
        )

    @staticmethod
    def _compact_plan(
        plan: str,
        max_steps: int = 6,
        max_chars: int = 900,
        fast_mode: bool = False,
    ) -> str:
        if fast_mode:
            max_steps = min(max_steps, 4)
            max_chars = min(max_chars, 450)
        lines = [line.strip() for line in plan.splitlines() if line.strip()]
        numbered = [
            line
            for line in lines
            if re.match(r"^(\d+[\.\)]|[-*])\s+", line)
        ]
        selected = numbered[:max_steps] if numbered else lines[:max_steps]
        compact = "\n".join(selected).strip()
        if len(compact) <= max_chars:
            return compact
        return compact[:max_chars].rsplit(" ", 1)[0].rstrip() + "..."

    @staticmethod
    def _fallback_plan(task: str, compact_plan: str, fast_mode: bool = False) -> str:
        if fast_mode:
            return (
                f"1. Build the smallest runnable implementation for: {task}\n"
                "2. Prefer one Python file.\n"
                "3. Use direct standard-library code and skip optional complexity.\n"
                "4. Output only runnable code."
            )
        first_step = compact_plan.splitlines()[0] if compact_plan else ""
        if first_step:
            return (
                f"1. Build the smallest runnable implementation for: {task}\n"
                f"2. Prioritize this core direction: {first_step}\n"
                "3. Keep it to one Python file unless multiple files are strictly necessary.\n"
                "4. Prefer straightforward data structures and standard-library modules.\n"
                "5. Make the code executable without extra explanation."
            )
        return (
            f"1. Build the smallest runnable implementation for: {task}\n"
            "2. Keep it to one Python file unless multiple files are strictly necessary.\n"
            "3. Prefer straightforward data structures and standard-library modules.\n"
            "4. Make the code executable without extra explanation."
        )

    @staticmethod
    def _review_suggests_changes(review: str) -> bool:
        normalized = review.strip().lower()
        if not normalized:
            return False
        if normalized.startswith("no issues found"):
            return False
        if "no issues found." in normalized and "findings:" not in normalized:
            return False
        return True

    def _validate_successful_output(self, task: str, code: str) -> str:
        if is_knowledge_base_task(task):
            return self._validate_knowledge_base_ingester(code)
        return ""

    def _validate_knowledge_base_ingester(self, code: str) -> str:
        scratch_root = Path.cwd() / ".agent_system_runs"
        scratch_root.mkdir(parents=True, exist_ok=True)
        temp_dir = scratch_root / f"validator-{uuid.uuid4().hex}"
        temp_dir.mkdir(parents=True, exist_ok=False)
        try:
            script_path = temp_dir / "candidate.py"
            raw_dir = temp_dir / "raw"
            vault_dir = temp_dir / "vault"
            raw_dir.mkdir(parents=True, exist_ok=True)
            vault_dir.mkdir(parents=True, exist_ok=True)
            script_path.write_text(code, encoding="utf-8")
            (raw_dir / "sample.md").write_text(knowledge_base_validation_sample(), encoding="utf-8")
            try:
                completed = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=max(12, self.settings.execution_timeout_seconds * 2),
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return "Semantic validation failed: generated knowledge-base script timed out on a small sample input."

            if completed.returncode != 0:
                stderr = (completed.stderr or completed.stdout).strip()
                return (
                    "Semantic validation failed: generated knowledge-base script did not run successfully on a small sample input.\n"
                    f"Validation stderr/stdout:\n{stderr or '[no output]'}"
                )

            errors = inspect_knowledge_base_artifacts(temp_dir)
            if not errors:
                return ""
            return "Semantic validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a multi-agent coding system against a Python task."
    )
    parser.add_argument("--task", help="The coding task to execute.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Maximum debug iterations. Defaults to MAX_DEBUG_ITERATIONS.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the final generated Python code.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use a shorter planner-to-coder path and more aggressive simplification.",
    )
    parser.add_argument(
        "--student-mode",
        action="store_true",
        help="Return beginner-friendly learning explanations for under-resourced students.",
    )
    parser.add_argument(
        "--budget-mode",
        action="store_true",
        help="Use a quota-saving workflow with compact planning, at most one debug pass, and saved handoff artifacts.",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run local environment diagnostics instead of a coding task.",
    )
    parser.add_argument(
        "--doctor-live",
        action="store_true",
        help="When used with --doctor, probe Claude/Codex with real authenticated CLI calls.",
    )
    parser.add_argument(
        "--doctor-output",
        type=Path,
        default=None,
        help="When used with --doctor, save the report to a .md or .json file.",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run offline benchmark/eval checks instead of a coding task.",
    )
    parser.add_argument(
        "--benchmark-output",
        type=Path,
        default=None,
        help="When used with --benchmark, save the report to a .md or .json file.",
    )
    parser.add_argument(
        "--session-dir",
        type=Path,
        default=None,
        help="Optional directory for saved run sessions and handoff summaries.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.doctor:
        if args.task or args.benchmark:
            parser.error("--doctor cannot be combined with --task or --benchmark.")
        return run_doctor(live=args.doctor_live, output_path=args.doctor_output)
    if args.benchmark:
        if args.task:
            parser.error("--benchmark cannot be combined with --task.")
        return run_benchmarks(output_path=args.benchmark_output)
    if not args.task:
        parser.error("--task is required unless --doctor or --benchmark is used.")
    if args.doctor_output is not None:
        parser.error("--doctor-output requires --doctor.")
    if args.benchmark_output is not None:
        parser.error("--benchmark-output requires --benchmark.")

    controller = Controller()
    recorder = SessionRecorder(
        task=args.task,
        backend=controller.settings.backend,
        fast_mode=args.fast or args.budget_mode or controller.settings.fast_mode or controller.settings.budget_mode,
        iterations=args.iterations,
        root_dir=args.session_dir,
    )

    try:
        summary = controller.run(
            task=args.task,
            iterations=args.iterations,
            fast_mode=True if args.fast else None,
            student_mode=True if args.student_mode else None,
            budget_mode=True if args.budget_mode else None,
            on_status=recorder.update,
        )
    except LLMError as exc:
        recorder.fail(str(exc))
        parser.error(str(exc))
        return 2
    except Exception as exc:
        recorder.fail(str(exc))
        raise

    recorder.finish(summary)
    recorder.save_report_aliases()

    print("=== PLAN ===")
    print(summary.plan)
    print()
    print("=== STATUS ===")
    print(
        f"success={summary.success} iterations_used={summary.iterations_used}"
    )
    print()
    print("=== REVIEW ===")
    print(summary.review)
    print()
    print("=== FINAL CODE ===")
    print(summary.final_code)

    if args.output is not None:
        args.output.write_text(summary.final_code, encoding="utf-8")
        print()
        print(f"Wrote final code to {args.output}")

    print()
    print(f"Saved session to {recorder.session_dir}")
    print(f"Handoff summary: {recorder.session_dir / 'handoff.md'}")

    return 0
