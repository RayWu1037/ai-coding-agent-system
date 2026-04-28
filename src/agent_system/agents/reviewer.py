from __future__ import annotations

from agent_system.agents.base import BaseAgent, AgentResult
from agent_system.prompts import REVIEWER_SYSTEM_PROMPT


class ReviewerAgent(BaseAgent):
    def run(self, task: str, code: str) -> AgentResult:
        user = f"Task:\n{task}\n\nFinal code:\n{code}"
        return self._call_debug_and_review(REVIEWER_SYSTEM_PROMPT, user)
