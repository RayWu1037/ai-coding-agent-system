from __future__ import annotations

import argparse
import os
from pathlib import Path

from agent_system.controller import Controller
from agent_system.integrations.gitlab import (
    build_agent_task,
    build_gitlab_comment,
    load_issue,
)
from agent_system.sessions import SessionRecorder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run AgentRelay from a GitLab issue JSON payload."
    )
    parser.add_argument(
        "--issue",
        type=Path,
        required=True,
        help="Path to a GitLab issue JSON export or demo fixture.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Maximum debug iterations. Defaults to MAX_DEBUG_ITERATIONS.",
    )
    parser.add_argument(
        "--session-dir",
        type=Path,
        default=None,
        help="Optional directory for saved run sessions and handoff summaries.",
    )
    parser.add_argument(
        "--demo-mode",
        action="store_true",
        help="Force deterministic offline demo mode for judging walkthroughs.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.demo_mode:
        os.environ["AGENT_DEMO_MODE"] = "1"

    issue = load_issue(args.issue)
    task = build_agent_task(issue)
    controller = Controller()
    recorder = SessionRecorder(
        task=task,
        backend=controller.settings.backend,
        fast_mode=controller.settings.fast_mode,
        iterations=args.iterations,
        root_dir=args.session_dir,
    )

    summary = controller.run(
        task=task,
        iterations=args.iterations,
        on_status=recorder.update,
        recorder=recorder,
    )
    recorder.finish(summary)
    recorder.save_report_aliases()

    comment = build_gitlab_comment(
        issue,
        success=summary.success,
        session_dir=str(recorder.session_dir),
        handoff_path=str(recorder.session_dir / "handoff.md"),
    )

    print("=== GITLAB ISSUE ===")
    print(issue.reference)
    print()
    print("=== AGENT TASK ===")
    print(task)
    print()
    print("=== STATUS ===")
    print(f"success={summary.success} iterations_used={summary.iterations_used}")
    print()
    print("=== GITLAB COMMENT DRAFT ===")
    print(comment)
    print()
    print(f"Saved session to {recorder.session_dir}")
    print(f"Handoff summary: {recorder.session_dir / 'handoff.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
