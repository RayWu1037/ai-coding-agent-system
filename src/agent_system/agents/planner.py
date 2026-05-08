from __future__ import annotations

from agent_system.agents.base import BaseAgent, AgentResult
from agent_system.prompts import PLANNER_SYSTEM_PROMPT


class PlannerAgent(BaseAgent):
    def run(self, task: str, student_mode: bool = False, budget_mode: bool = False) -> AgentResult:
        mode_guidance = ""
        if student_mode:
            mode_guidance += (
                "Write the plan as a beginner-friendly learning plan. "
                "Avoid unexplained jargon and make each step teach the student what will happen. "
            )
        if budget_mode:
            mode_guidance += (
                "Keep the plan especially short because this run is budget-aware and should avoid unnecessary model calls. "
            )
        user = (
            f"Task:\n{task}\n\n"
            "Provide a concise implementation plan with at most 6 numbered steps. "
            "Keep every step short."
        )
        if mode_guidance:
            user = f"{user}\n\nAccessBridge mode guidance:\n{mode_guidance}"
        return self._call_plan_and_code(PLANNER_SYSTEM_PROMPT, user)
