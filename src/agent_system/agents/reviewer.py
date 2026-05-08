from __future__ import annotations

from agent_system.agents.base import BaseAgent, AgentResult
from agent_system.prompts import REVIEWER_SYSTEM_PROMPT
from agent_system.task_profiles import reviewer_guidance


class ReviewerAgent(BaseAgent):
    def run(
        self,
        task: str,
        code: str,
        student_mode: bool = False,
        budget_mode: bool = False,
    ) -> AgentResult:
        user = f"Task:\n{task}\n\nFinal code:\n{code}"
        task_guidance = reviewer_guidance(task)
        if task_guidance:
            user = f"{user}\n\n{task_guidance}"
        if student_mode:
            user = (
                f"{user}\n\nAccessBridge student-mode review requirements:\n"
                "Return a beginner-friendly explanation with exactly these section headings:\n"
                "What was wrong\n"
                "What was fixed\n"
                "What you learned\n"
                "Use plain language, avoid unexplained jargon, and explain the debugging lesson rather than only judging code quality."
            )
        if budget_mode:
            user = (
                f"{user}\n\nAccessBridge budget-mode review requirements:\n"
                "Keep the review concise so the student can continue without spending extra usage on repeated prompts."
            )
        return self._call_debug_and_review(REVIEWER_SYSTEM_PROMPT, user)
