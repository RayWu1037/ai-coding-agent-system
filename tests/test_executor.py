import shutil
import sys
import unittest
import uuid
from pathlib import Path

from agent_system.tools.executor import PythonExecutor


class ExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path.cwd() / ".test_executor" / uuid.uuid4().hex
        self.workspace.mkdir(parents=True, exist_ok=False)

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_executor_runs_in_generated_script_directory(self) -> None:
        executor = PythonExecutor(
            timeout_seconds=5,
            python_command=sys.executable,
            workspace_root=self.workspace,
        )
        code = (
            "from pathlib import Path\n"
            "Path('relative_output.txt').write_text('ok', encoding='utf-8')\n"
            "print(Path.cwd().name)\n"
        )

        result = executor.run(code)

        self.assertTrue(result.succeeded, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), result.script_path.parent.name)


if __name__ == "__main__":
    unittest.main()
