from __future__ import annotations

from agent_system.agents.base import BaseAgent, AgentResult
from agent_system.prompts import CODER_SYSTEM_PROMPT


class CoderAgent(BaseAgent):
    def run(self, task: str, plan: str) -> AgentResult:
        user = (
            f"Task:\n{task}\n\n"
            f"Implementation plan:\n{plan}\n\n"
            "Generate the full Python solution now."
        )
        return self._call_plan_and_code(CODER_SYSTEM_PROMPT, user)
