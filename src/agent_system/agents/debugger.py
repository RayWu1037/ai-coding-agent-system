from __future__ import annotations

from agent_system.agents.base import BaseAgent, AgentResult
from agent_system.prompts import DEBUGGER_SYSTEM_PROMPT
from agent_system.task_profiles import debugger_guidance


class DebuggerAgent(BaseAgent):
    def run(
        self,
        task: str,
        code: str,
        output: str,
        error: str,
        review_feedback: str | None = None,
    ) -> AgentResult:
        review_section = ""
        if review_feedback:
            review_section = f"\n\nReviewer feedback:\n{review_feedback}\n"
        task_guidance = debugger_guidance(task)
        user = (
            f"Original task:\n{task}\n\n"
            f"Current code:\n{code}\n\n"
            f"Program stdout:\n{output or '[no output]'}\n\n"
            f"Program stderr:\n{error or '[no error text]'}\n\n"
            f"{review_section}"
            "Fix the code and return the full corrected Python file."
        )
        if task_guidance:
            user = f"{user}\n\n{task_guidance}"
        return self._call_debug_and_review(DEBUGGER_SYSTEM_PROMPT, user)
