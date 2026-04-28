import json
import math
import os
from datetime import datetime
from typing import Any, Dict, Optional

from agents.langchain_runtime import LangChainAgentRuntime
from agents.tools import AgentContextTools
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SLMService:
    """Bounded intelligence adapter with LangChain-first structured output and deterministic fallbacks."""

    DEFAULT_MODEL = "gpt-4o-mini"
    TIMEOUT_SECONDS = 5.0
    TEMPERATURE = 0.2

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        requested_model = os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL).strip() or self.DEFAULT_MODEL
        self.model = self.DEFAULT_MODEL if requested_model != self.DEFAULT_MODEL else requested_model
        self.disabled_reason: Optional[str] = None
        self.context_tools = AgentContextTools()
        self.runtime = LangChainAgentRuntime(
            api_key=self.api_key,
            model=self.model,
            timeout_seconds=self.TIMEOUT_SECONDS,
            temperature=self.TEMPERATURE,
            context_tools=self.context_tools,
        )

        if requested_model != self.DEFAULT_MODEL:
            logger.warning(
                "[SLM] Unsupported OPENAI_MODEL '%s'. Falling back to required model '%s'.",
                requested_model,
                self.DEFAULT_MODEL,
            )

        if self.runtime.disabled_reason:
            self.disabled_reason = self.runtime.disabled_reason

    def generate_json(self, system_prompt: str, payload: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Generate strict JSON for an agent chain or return a deterministic fallback."""
        if self.disabled_reason or not self.runtime.is_available:
            self._log_usage(agent_name, payload, "fallback", None)
            return self.fallback_response(agent_name, payload)

        estimated_tokens = self._estimate_tokens(system_prompt, payload)

        try:
            parsed = self.runtime.run_agent(agent_name, system_prompt, payload)
            self._log_usage(agent_name, payload, "success", None, estimated_tokens)
            return parsed
        except Exception as exc:  # pragma: no cover - runtime safety
            self.disabled_reason = str(exc)
            self.runtime.disabled_reason = str(exc)
            logger.warning("[SLM] Falling back for agent=%s error=%s", agent_name, exc)
            self._log_usage(agent_name, payload, "fallback", None, estimated_tokens)
            return self.fallback_response(agent_name, payload)

    def safe_parse(self, text: Any) -> Optional[Dict[str, Any]]:
        if isinstance(text, dict):
            return text
        if not isinstance(text, str):
            return None

        candidate = text.strip()
        if not candidate:
            return None

        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                parsed = json.loads(candidate[start : end + 1])
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None

    def fallback_response(self, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        event_type = str(payload.get("event_type", "UNKNOWN")).upper()
        severity = str(payload.get("severity", "WARNING")).upper()
        risk_score = int(payload.get("risk_score", payload.get("score", 0)) or 0)
        location = self._format_location(payload)

        if agent_name == "triage":
            return {
                "dashboard_title": f"{event_type.title()} Alert",
                "operator_summary": f"{severity.title()} {event_type.lower().replace('_', ' ')} detected at {location}.",
                "risk_explanation": f"System rules assigned severity {severity} with risk score {risk_score}.",
                "recommended_priority": self._priority_label(severity, risk_score),
                "tts_message": f"{severity.title()} {event_type.lower().replace('_', ' ')} at {location}.",
                "requires_operator_review": severity in {"WARNING", "CRITICAL"},
            }

        if agent_name == "timeline":
            detections = int(payload.get("detections_count", 1) or 1)
            return {
                "incident_title": f"{event_type.title()} Incident at {location}",
                "timeline_summary": f"{detections} detections recorded for this incident window.",
                "recommended_next_step": "Continue monitoring and preserve evidence while following the system guidance.",
            }

        if agent_name == "actions":
            action_plan = payload.get("base_actions") or self._default_actions(event_type)
            subtype = str(payload.get("subtype") or event_type.lower()).replace("_", " ")
            risk_level = str(payload.get("risk_level", "MEDIUM")).upper()
            recommended_action = str(payload.get("recommended_action") or "").strip()
            incident_summary = str(
                ((payload.get("incident_context") or {}).get("timeline_summary"))
                or ""
            ).strip()
            summary_suffix = f" {incident_summary}" if incident_summary else ""
            escalation_hint = f"Escalate immediately if the {subtype} remains active at {location}"
            if risk_level == "HIGH" or severity == "CRITICAL":
                escalation_hint += ", additional subjects appear, or responders need support."
            else:
                escalation_hint += " or the system confidence increases."

            return {
                "action_plan": action_plan,
                "operator_note": (
                    f"Follow {event_type.lower().replace('_', ' ')} procedure for the {subtype} event at {location}."
                    f"{f' Priority action: {recommended_action}.' if recommended_action else ''}"
                    f"{summary_suffix}"
                ),
                "escalation_hint": escalation_hint,
            }

        return {"message": "Fallback response", "payload": payload}

    def _log_usage(
        self,
        agent_name: str,
        payload: Dict[str, Any],
        status: str,
        response: Any = None,
        estimated_tokens: Optional[int] = None,
    ) -> None:
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None) if usage else None
        output_tokens = getattr(usage, "output_tokens", None) if usage else None
        total_tokens = getattr(usage, "total_tokens", None) if usage else None

        if total_tokens is None:
            total_tokens = estimated_tokens or self._estimate_tokens("", payload)

        logger.info(
            "[SLM_USAGE] %s",
            json.dumps(
                {
                    "agent": agent_name,
                    "camera": payload.get("camera_id") or payload.get("camera"),
                    "event_type": payload.get("event_type"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": status,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens_estimate": total_tokens,
                }
            ),
        )

    @staticmethod
    def _estimate_tokens(system_prompt: str, payload: Dict[str, Any]) -> int:
        raw = f"{system_prompt}\n{json.dumps(payload, ensure_ascii=True)}"
        return max(1, math.ceil(len(raw) / 4))

    @staticmethod
    def _priority_label(severity: str, risk_score: int) -> str:
        if severity == "CRITICAL" or risk_score >= 90:
            return "IMMEDIATE"
        if risk_score >= 70:
            return "HIGH"
        return "STANDARD"

    @staticmethod
    def _format_location(payload: Dict[str, Any]) -> str:
        parts = [
            str(payload.get("camera_name") or payload.get("camera_id") or "Camera 1"),
            str(payload.get("sector") or "").strip(),
            str(payload.get("area") or "").strip(),
        ]
        return ", ".join([part for part in parts if part])

    @staticmethod
    def _default_actions(event_type: str) -> list[str]:
        if event_type == "WEAPON":
            return ["Focus camera", "Dispatch guard", "Preserve evidence"]
        if event_type == "FIGHT":
            return ["Dispatch guard", "Monitor individuals", "Confirm resolution"]
        if event_type == "ABANDONED_LUGGAGE":
            return ["Inspect item", "Monitor area", "Escalate if needed"]
        return ["Monitor scene", "Review event details", "Escalate if needed"]

