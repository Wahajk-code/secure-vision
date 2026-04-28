from __future__ import annotations

import json
from typing import Any, Dict, Optional, Type

from utils.logger import setup_logger

from agents.schemas import ActionsOutput, TimelineOutput, TriageOutput
from agents.tools import AgentContextTools

logger = setup_logger(__name__)

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - runtime safety
    ChatPromptTemplate = None
    ChatOpenAI = None


class LangChainAgentRuntime:
    """Bounded LangChain runtime for the triage, timeline, and operator action chains."""

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        temperature: float,
        context_tools: AgentContextTools | None = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.context_tools = context_tools or AgentContextTools()
        self.disabled_reason: Optional[str] = None
        self.client = None

        if not self.api_key:
            self.disabled_reason = "OPENAI_API_KEY missing"
            return
        if ChatOpenAI is None or ChatPromptTemplate is None:
            self.disabled_reason = "LangChain dependencies missing"
            return

        try:
            self.client = ChatOpenAI(
                api_key=self.api_key,
                model=self.model,
                timeout=self.timeout_seconds,
                temperature=self.temperature,
            )
        except Exception as exc:  # pragma: no cover - runtime safety
            self.disabled_reason = str(exc)
            logger.error("[LANGCHAIN] Failed to initialize runtime: %s", exc)

    @property
    def is_available(self) -> bool:
        return self.client is not None and self.disabled_reason is None

    def run_agent(self, agent_name: str, system_prompt: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_available:
            raise RuntimeError(self.disabled_reason or "LangChain runtime unavailable")

        schema = self._schema_for_agent(agent_name)
        prompt = self._prompt_for_agent(agent_name)
        context = self._context_for_agent(agent_name, payload)
        structured_model = self.client.with_structured_output(schema)
        chain = prompt | structured_model

        try:
            result = chain.invoke(
                {
                    "system_prompt": system_prompt.strip(),
                    "payload_json": json.dumps(payload, ensure_ascii=True, sort_keys=True),
                    "context_json": json.dumps(context, ensure_ascii=True, sort_keys=True),
                }
            )
        except Exception as exc:  # pragma: no cover - runtime safety
            self.disabled_reason = str(exc)
            raise

        if hasattr(result, "model_dump"):
            return result.model_dump()
        if isinstance(result, dict):
            return result
        raise ValueError(f"Unsupported LangChain result type for agent={agent_name}: {type(result)!r}")

    def _context_for_agent(self, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        camera_context = self.context_tools.get_camera_context(payload)
        rule_context = self.context_tools.get_rule_context(payload)
        incident_context = self.context_tools.get_incident_context(payload)
        operator_constraints = self.context_tools.get_operator_constraints(payload)

        if agent_name == "triage":
            return {
                "camera_context": camera_context,
                "rule_context": rule_context,
            }
        if agent_name == "timeline":
            return {
                "camera_context": camera_context,
                "rule_context": rule_context,
                "incident_context": incident_context,
            }
        if agent_name == "actions":
            return {
                "camera_context": camera_context,
                "rule_context": rule_context,
                "incident_context": incident_context,
                "operator_constraints": operator_constraints,
                "triage_context": payload.get("triage_context") or {},
            }
        return {
            "camera_context": camera_context,
            "rule_context": rule_context,
            "incident_context": incident_context,
            "operator_constraints": operator_constraints,
        }

    @staticmethod
    def _prompt_for_agent(agent_name: str) -> ChatPromptTemplate:
        role_line = {
            "triage": "You are the SecureVision Triage Agent in a bounded multi-agent incident workflow.",
            "timeline": "You are the SecureVision Incident Timeline Agent in a bounded multi-agent incident workflow.",
            "actions": "You are the SecureVision Operator Action Agent in a bounded multi-agent incident workflow.",
        }.get(agent_name, "You are a SecureVision bounded incident agent.")

        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        f"{role_line} "
                        "You must preserve all deterministic safety facts from the rule engine. "
                        "{system_prompt}"
                    ),
                ),
                (
                    "human",
                    (
                        "Normalized payload JSON:\n{payload_json}\n\n"
                        "Deterministic context and tool outputs JSON:\n{context_json}\n\n"
                        "Return only the structured response for your role."
                    ),
                ),
            ]
        )

    @staticmethod
    def _schema_for_agent(agent_name: str) -> Type[Any]:
        if agent_name == "triage":
            return TriageOutput
        if agent_name == "timeline":
            return TimelineOutput
        if agent_name == "actions":
            return ActionsOutput
        raise ValueError(f"Unsupported agent_name '{agent_name}' for LangChain runtime")
