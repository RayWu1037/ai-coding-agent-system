import unittest

from agent_system.llm import AggregateLLMError, LLMError, LLMRegistry, Message


class _FakeClient:
    def __init__(self, response: str | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error

    def complete(self, _message: Message) -> str:
        if self.error is not None:
            raise self.error
        return self.response or ""


class LLMRegistryTests(unittest.TestCase):
    def _registry(self) -> LLMRegistry:
        registry = object.__new__(LLMRegistry)
        registry._settings = type("Settings", (), {"backend": "cli"})()
        registry._claude_cli = None
        registry._codex_cli = None
        registry._anthropic = None
        registry._openai = None
        return registry

    def test_plan_and_code_falls_back_after_cli_failure(self) -> None:
        registry = self._registry()
        registry._claude_cli = _FakeClient(error=LLMError("quota exceeded"))
        registry._codex_cli = _FakeClient(response="print('ok')")

        result = registry.plan_and_code(Message(system="s", user="u"))

        self.assertEqual(result, "print('ok')")

    def test_debug_and_review_aggregates_all_failures(self) -> None:
        registry = self._registry()
        registry._claude_cli = _FakeClient(error=LLMError("rate limited"))
        registry._codex_cli = _FakeClient(error=TimeoutError("timed out"))

        with self.assertRaises(AggregateLLMError) as context:
            registry.debug_and_review(Message(system="s", user="u"))

        self.assertIn("Codex CLI", str(context.exception))
        self.assertIn("Claude CLI", str(context.exception))


if __name__ == "__main__":
    unittest.main()
