from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from agent_system.agents.coder import CoderAgent
from agent_system.agents.debugger import DebuggerAgent
from agent_system.agents.planner import PlannerAgent
from agent_system.agents.reviewer import ReviewerAgent
from agent_system.config import load_settings
from agent_system.llm import LLMError, LLMRegistry
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
        on_status: StatusCallback | None = None,
    ) -> RunSummary:
        max_iterations = iterations or self.settings.max_debug_iterations
        self._notify(on_status, "planning", "Building implementation plan.")
        plan = self.planner.run(task).content
        self._notify(on_status, "coding", "Generating initial solution.")
        code = self.coder.run(task, plan).content
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
        self._notify(on_status, "done", "Run complete.")
        return RunSummary(
            plan=plan,
            final_code=code,
            review=review,
            iterations_used=iterations_used,
            success=success,
        )

    @staticmethod
    def _notify(callback: StatusCallback | None, stage: str, message: str) -> None:
        if callback is not None:
            callback(stage, message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a multi-agent coding system against a Python task."
    )
    parser.add_argument("--task", required=True, help="The coding task to execute.")
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
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        summary = Controller().run(task=args.task, iterations=args.iterations)
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
