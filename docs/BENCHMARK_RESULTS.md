# Benchmark Results

Offline benchmark results for the multi-agent coding harness.
Run with: `.\run_cli.bat --benchmark --benchmark-output reports\benchmarks.md`

---

## 2026-04-28

- **Python:** 3.13.12
- **Commit:** `d53a183`
- **Result:** 4/4 passed

| Status | Benchmark | Detail |
| --- | --- | --- |
| `ok` | executor_isolation | Executor uses the generated script directory as cwd. |
| `ok` | knowledge_base_good_fixture | Validator accepts a clean knowledge-base artifact. |
| `ok` | knowledge_base_bad_fixture | Validator rejects malformed knowledge-base artifacts. |
| `ok` | todo_fixture | Local file-based CLI-style workload runs correctly. |

### Benchmark Descriptions

| Benchmark | What it checks |
| --- | --- |
| `executor_isolation` | Generated code runs with its own directory as cwd, not the caller's cwd. |
| `knowledge_base_good_fixture` | Validator correctly accepts a clean KB artifact (valid title, links, index). |
| `knowledge_base_bad_fixture` | Validator correctly rejects a bad KB artifact (title drift, noisy concepts). |
| `todo_fixture` | A file-based CLI-style workload (JSON read/write) executes correctly end-to-end. |
