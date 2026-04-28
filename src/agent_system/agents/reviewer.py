from __future__ import annotations

from agent_system.agents.base import BaseAgent, AgentResult
from agent_system.prompts import REVIEWER_SYSTEM_PROMPT
from agent_system.task_profiles import reviewer_guidance


class ReviewerAgent(BaseAgent):
    def run(self, task: str, code: str) -> AgentResult:
        user = f"Task:\n{task}\n\nFinal code:\n{code}"
        task_guidance = reviewer_guidance(task)
        if task_guidance:
            user = f"{user}\n\n{task_guidance}"
        return self._call_debug_and_review(REVIEWER_SYSTEM_PROMPT, user)
