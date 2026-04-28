from __future__ import annotations

from agent_system.agents.base import BaseAgent, AgentResult
from agent_system.prompts import DEBUGGER_SYSTEM_PROMPT


class DebuggerAgent(BaseAgent):
    def run(self, task: str, code: str, output: str, error: str) -> AgentResult:
        user = (
            f"Original task:\n{task}\n\n"
            f"Current code:\n{code}\n\n"
            f"Program stdout:\n{output or '[no output]'}\n\n"
            f"Program stderr:\n{error or '[no error text]'}\n\n"
            "Fix the code and return the full corrected Python file."
        )
        return self._call_debug_and_review(DEBUGGER_SYSTEM_PROMPT, user)
