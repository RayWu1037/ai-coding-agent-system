from __future__ import annotations

from dataclasses import dataclass

from agent_system.llm import LLMRegistry, Message


@dataclass
class AgentResult:
    content: str


class BaseAgent:
    def __init__(self, llms: LLMRegistry) -> None:
        self.llms = llms

    def _call_plan_and_code(self, system: str, user: str) -> AgentResult:
        return AgentResult(self.llms.plan_and_code(Message(system=system, user=user)))

    def _call_debug_and_review(self, system: str, user: str) -> AgentResult:
        return AgentResult(self.llms.debug_and_review(Message(system=system, user=user)))
