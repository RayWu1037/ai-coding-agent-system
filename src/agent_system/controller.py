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
from agent_system.agents.debugger import DebuggerAgent
from agent_system.agents.planner import PlannerAgent
from agent_system.agents.reviewer import ReviewerAgent
from agent_system.config import load_settings
from agent_system.doctor import run_doctor
from agent_system.llm import LLMError, LLMRegistry
from agent_system.task_profiles import is_knowledge_base_task
from agent_system.tools.executor import PythonExecutor


@dataclass
class RunSummary:
    plan: str
    final_code: str
    review: str
    iterations_used: int
    success: bool


StatusCallback = Callable[[str, str], None]


class Controller:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.llms = LLMRegistry(self.settings)
        self.planner = PlannerAgent(self.llms)
        self.coder = CoderAgent(self.llms)
        self.debugger = DebuggerAgent(self.llms)
        self.reviewer = ReviewerAgent(self.llms)
        self.executor = PythonExecutor(
            timeout_seconds=self.settings.execution_timeout_seconds
        )

    def run(
        self,
        task: str,
        iterations: int | None = None,
        fast_mode: bool | None = None,
        on_status: StatusCallback | None = None,
    ) -> RunSummary:
        use_fast_mode = self.settings.fast_mode if fast_mode is None else fast_mode
        max_iterations = iterations or self.settings.max_debug_iterations
        review_repair_budget = 2 if not use_fast_mode else 1
        self._notify(on_status, "planning", "Building implementation plan.")
        plan = self.planner.run(task).content
        compact_plan = self._compact_plan(plan, fast_mode=use_fast_mode)
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
        success = False
        iterations_used = 0

        for index in range(max_iterations + 1):
            iterations_used = index + 1
            self._notify(
                on_status,
                "executing",
                f"Running generated code (attempt {iterations_used}/{max_iterations + 1}).",
            )
            result = self.executor.run(code)
            if result.succeeded:
                validation_feedback = self._validate_successful_output(task, code)
                if validation_feedback:
                    result.stderr = validation_feedback
                    result.returncode = 2
            if result.succeeded:
                success = True
                self._notify(
                    on_status,
                    "success",
                    f"Execution succeeded on attempt {iterations_used}.",
                )
                break
            if index == max_iterations:
                break
            self._notify(
                on_status,
                "debugging",
                f"Execution failed on attempt {iterations_used}; requesting fix.",
            )
            code = self.debugger.run(task, code, result.stdout, result.stderr).content

        self._notify(on_status, "reviewing", "Reviewing final code.")
        review = self.reviewer.run(task, code).content
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
            iterations_used += 1
            success = rerun.succeeded
            review_repair_budget -= 1
            self._notify(on_status, "reviewing", "Reviewing improved code.")
            review = self.reviewer.run(task, code).content
        self._notify(on_status, "done", "Run complete.")
        return RunSummary(
            plan=compact_plan,
            final_code=code,
            review=review,
            iterations_used=iterations_used,
            success=success,
        )

    @staticmethod
    def _notify(callback: StatusCallback | None, stage: str, message: str) -> None:
        if callback is not None:
            callback(stage, message)

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
            (raw_dir / "sample.md").write_text(_knowledge_base_validation_sample(), encoding="utf-8")
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

            errors = _inspect_knowledge_base_artifacts(temp_dir)
            if not errors:
                return ""
            return "Semantic validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def _knowledge_base_validation_sample() -> str:
    return """# AI Agent

An AI Agent can turn raw notes into linked wiki notes inside an Obsidian knowledge base.

## Core Idea

The system reads files from a raw folder, extracts stable concepts, and writes markdown notes with [[links]] into a wiki vault.

## Output Expectations

The generated note should keep the top-level title AI Agent and avoid generic concepts like Core Idea or Notes.
"""


def _inspect_knowledge_base_artifacts(root_dir: Path) -> list[str]:
    note_path = _find_generated_note(root_dir, "AI Agent.md")
    index_path = _find_generated_index(root_dir)
    note_files = sorted(
        path.name
        for path in root_dir.rglob("*.md")
        if path.name.lower() not in {"_index.md", "index.md"}
    )
    errors: list[str] = []

    if note_path is None:
        errors.append(
            "expected an output note named 'AI Agent.md' derived from the sample file's top-level H1; "
            f"found: {', '.join(note_files) if note_files else 'no note files'}"
        )
        return errors

    note_text = note_path.read_text(encoding="utf-8", errors="replace")
    if "# AI Agent" not in note_text:
        errors.append("generated note does not preserve the source title 'AI Agent' as the main H1")
    if "[[Notes. Concept]]" in note_text:
        errors.append("generated note contains malformed or low-value concept label 'Notes. Concept'")
    if "[[Core Idea]]" in note_text:
        errors.append("generated note promoted the generic subsection heading 'Core Idea' into a concept link")
    lowered_note = note_text.casefold()
    if "raw notes" not in lowered_note or "wiki notes" not in lowered_note:
        errors.append("generated note summary/body did not preserve the core relation between Raw Notes and Wiki Notes")

    if index_path is None:
        errors.append("knowledge-base index file was not created")
        return errors

    index_text = index_path.read_text(encoding="utf-8", errors="replace")
    if "[[AI Agent]]" not in index_text:
        errors.append("knowledge-base index does not link to [[AI Agent]]")
    return errors


def _find_generated_note(root_dir: Path, filename: str) -> Path | None:
    preferred_dirs = ["vault", "wiki", "notes"]
    for directory_name in preferred_dirs:
        candidate = root_dir / directory_name / filename
        if candidate.exists():
            return candidate
    for candidate in root_dir.rglob(filename):
        if candidate.is_file():
            return candidate
    return None


def _find_generated_index(root_dir: Path) -> Path | None:
    for directory_name in ["vault", "wiki", "notes"]:
        for filename in ["_index.md", "Index.md", "index.md"]:
            candidate = root_dir / directory_name / filename
            if candidate.exists():
                return candidate
    for filename in ["_index.md", "Index.md", "index.md"]:
        candidate = root_dir / filename
        if candidate.exists():
            return candidate
    return None


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
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.doctor:
        if args.task:
            parser.error("--doctor cannot be combined with --task.")
        return run_doctor(live=args.doctor_live, output_path=args.doctor_output)
    if not args.task:
        parser.error("--task is required unless --doctor is used.")
    if args.doctor_output is not None:
        parser.error("--doctor-output requires --doctor.")

    try:
        summary = Controller().run(
            task=args.task,
            iterations=args.iterations,
            fast_mode=args.fast,
        )
    except LLMError as exc:
        parser.error(str(exc))
        return 2

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

    return 0
