import shutil
import unittest
import uuid
from pathlib import Path

from agent_system.benchmarks import collect_benchmarks, write_benchmark_report


class BenchmarkTests(unittest.TestCase):
    def test_collect_benchmarks_returns_all_green(self) -> None:
        results = collect_benchmarks()
        self.assertTrue(results)
        self.assertTrue(all(result.status == "ok" for result in results))

    def test_write_benchmark_report_json(self) -> None:
        root = Path.cwd() / ".test_benchmarks" / uuid.uuid4().hex
        root.mkdir(parents=True, exist_ok=False)
        self.addCleanup(shutil.rmtree, root, True)
        output = root / "benchmarks.json"

        write_benchmark_report(output, collect_benchmarks())

        self.assertTrue(output.exists())
        self.assertIn('"results"', output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
