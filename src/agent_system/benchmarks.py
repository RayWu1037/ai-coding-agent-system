from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from agent_system.tools.executor import PythonExecutor
from agent_system.validation import inspect_knowledge_base_artifacts


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    status: str
    detail: str


def run_benchmarks(output_path: Path | None = None) -> int:
    results = collect_benchmarks()
    report = format_benchmark_report(results)
    print(report)
    if output_path is not None:
        write_benchmark_report(output_path, results)
        print(f"\nSaved benchmark report to {output_path}")
    return 1 if any(result.status == "fail" for result in results) else 0


def collect_benchmarks() -> list[BenchmarkResult]:
    return [
        _benchmark_executor_isolation(),
        _benchmark_kb_good_fixture(),
        _benchmark_kb_bad_fixture(),
        _benchmark_todo_fixture(),
    ]


def format_benchmark_report(results: list[BenchmarkResult]) -> str:
    lines = [
        "=== BENCHMARKS ===",
        "",
    ]
    for result in results:
        lines.append(f"[{result.status.upper():4}] {result.name}: {result.detail}")
    return "\n".join(lines)


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def write_benchmark_report(output_path: Path, results: list[BenchmarkResult]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    commit = _git_commit()
    if output_path.suffix.lower() == ".json":
        payload = {
            "run_at": run_at,
            "python": python_ver,
            "commit": commit,
            "results": [asdict(result) for result in results],
        }
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return
    passed = sum(1 for r in results if r.status == "ok")
    total = len(results)
    lines = [
        "# Benchmark Report",
        "",
        f"- **Run at:** {run_at}",
        f"- **Python:** {python_ver}",
        f"- **Commit:** `{commit}`",
        f"- **Result:** {passed}/{total} passed",
        "",
        "| Status | Benchmark | Detail |",
        "| --- | --- | --- |",
    ]
    for result in results:
        lines.append(f"| `{result.status}` | {result.name} | {result.detail.replace(chr(10), '<br>')} |")
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _benchmark_executor_isolation() -> BenchmarkResult:
    root = _make_temp_root("bench-executor")
    try:
        executor = PythonExecutor(
            timeout_seconds=5,
            python_command=sys.executable,
            workspace_root=root,
        )
        code = "from pathlib import Path\nprint(Path.cwd().name)\n"
        result = executor.run(code)
        if result.succeeded and result.stdout.strip() == result.script_path.parent.name:
            return BenchmarkResult("executor_isolation", "ok", "Executor uses the generated script directory as cwd.")
        return BenchmarkResult("executor_isolation", "fail", result.stderr.strip() or result.stdout.strip() or "Unexpected executor output.")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _benchmark_kb_good_fixture() -> BenchmarkResult:
    root = _make_temp_root("bench-kb-good")
    try:
        notes_dir = root / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        (notes_dir / "AI Agent.md").write_text(
            "\n".join(
                [
                    "# AI Agent",
                    "",
                    "An AI Agent turns Raw Notes into Wiki Notes inside an Obsidian vault.",
                    "",
                    "## Concepts",
                    "",
                    "[[AI Agent]] - [[Raw Notes]] - [[Wiki Notes]]",
                ]
            ),
            encoding="utf-8",
        )
        (notes_dir / "Index.md").write_text("- [[AI Agent]]\n", encoding="utf-8")
        errors = inspect_knowledge_base_artifacts(root)
        if not errors:
            return BenchmarkResult("knowledge_base_good_fixture", "ok", "Validator accepts a clean knowledge-base artifact.")
        return BenchmarkResult("knowledge_base_good_fixture", "fail", "; ".join(errors))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _benchmark_kb_bad_fixture() -> BenchmarkResult:
    root = _make_temp_root("bench-kb-bad")
    try:
        notes_dir = root / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        (notes_dir / "Core Idea.md").write_text(
            "\n".join(
                [
                    "# Core Idea",
                    "",
                    "[[AI Agent]] - [[Notes. Concept]] - [[Core Idea]]",
                ]
            ),
            encoding="utf-8",
        )
        (notes_dir / "Index.md").write_text("- [[Core Idea]]\n", encoding="utf-8")
        errors = inspect_knowledge_base_artifacts(root)
        if errors:
            return BenchmarkResult("knowledge_base_bad_fixture", "ok", "Validator rejects malformed knowledge-base artifacts.")
        return BenchmarkResult("knowledge_base_bad_fixture", "fail", "Validator unexpectedly accepted a bad artifact.")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _benchmark_todo_fixture() -> BenchmarkResult:
    root = _make_temp_root("bench-todo")
    try:
        executor = PythonExecutor(
            timeout_seconds=5,
            python_command=sys.executable,
            workspace_root=root,
        )
        code = (
            "import json\n"
            "from pathlib import Path\n"
            "path = Path('todos.json')\n"
            "data = [{'id': 1, 'title': 'Buy milk', 'done': False}]\n"
            "path.write_text(json.dumps(data), encoding='utf-8')\n"
            "loaded = json.loads(path.read_text(encoding='utf-8'))\n"
            "print(loaded[0]['title'])\n"
        )
        result = executor.run(code)
        if result.succeeded and result.stdout.strip() == "Buy milk":
            return BenchmarkResult("todo_fixture", "ok", "Local file-based CLI-style workload runs correctly.")
        return BenchmarkResult("todo_fixture", "fail", result.stderr.strip() or result.stdout.strip() or "Unexpected todo fixture output.")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _make_temp_root(prefix: str) -> Path:
    root = Path.cwd() / ".agent_system_runs" / f"{prefix}-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root
