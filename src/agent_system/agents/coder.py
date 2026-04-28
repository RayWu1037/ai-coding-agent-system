from __future__ import annotations

from agent_system.agents.base import BaseAgent, AgentResult
from agent_system.prompts import CODER_SYSTEM_PROMPT
from agent_system.task_profiles import coder_guidance


class CoderAgent(BaseAgent):
    def run(self, task: str, plan: str) -> AgentResult:
        task_guidance = coder_guidance(task)
        user = (
            f"Task:\n{task}\n\n"
            f"Implementation plan:\n{plan}\n\n"
            "Generate the full Python solution now. "
            "If the task implies multiple files, include all files in one runnable Python file unless a multi-file layout is absolutely required. "
            "Prefer a local-only implementation and avoid requiring API keys unless the user explicitly requested them."
        )
        if task_guidance:
            user = f"{user}\n\n{task_guidance}"
        return self._call_plan_and_code(CODER_SYSTEM_PROMPT, user)
