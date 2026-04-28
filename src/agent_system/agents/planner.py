from __future__ import annotations

from agent_system.agents.base import BaseAgent, AgentResult
from agent_system.prompts import PLANNER_SYSTEM_PROMPT


class PlannerAgent(BaseAgent):
    def run(self, task: str) -> AgentResult:
        user = (
            f"Task:\n{task}\n\n"
            "Provide a concise implementation plan with at most 6 numbered steps. "
            "Keep every step short."
        )
        return self._call_plan_and_code(PLANNER_SYSTEM_PROMPT, user)
