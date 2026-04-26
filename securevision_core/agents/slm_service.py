import json
import math
import os
from datetime import datetime
from typing import Any, Dict, Optional

from utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - safe fallback when dependency is missing
    OpenAI = None


class SLMService:
    """Small language model helper for strict JSON agent outputs with safe fallbacks."""

    DEFAULT_MODEL = "gpt-4o-mini"
    TIMEOUT_SECONDS = 5.0
    TEMPERATURE = 0.2

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        requested_model = os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL).strip() or self.DEFAULT_MODEL
        self.model = self.DEFAULT_MODEL if requested_model != self.DEFAULT_MODEL else requested_model
        self.client = None
        self.disabled_reason: Optional[str] = None

        if requested_model != self.DEFAULT_MODEL:
            logger.warning(
                "[SLM] Unsupported OPENAI_MODEL '%s'. Falling back to required model '%s'.",
                requested_model,
                self.DEFAULT_MODEL,
            )

        if self.api_key and OpenAI is not None:
            try:
                self.client = OpenAI(api_key=self.api_key, timeout=self.TIMEOUT_SECONDS)
            except Exception as exc:  # pragma: no cover - runtime safety
                logger.error("[SLM] Failed to initialize OpenAI client: %s", exc)
                self.client = None

    def generate_json(self, system_prompt: str, payload: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Generate strict JSON for an agent or return a deterministic fallback."""
        if self.disabled_reason or not self.client or not self.api_key:
            self._log_usage(agent_name, payload, "fallback", None)
            return self.fallback_response(agent_name, payload)

        schema = self._schema_for_agent(agent_name)
        estimated_tokens = self._estimate_tokens(system_prompt, payload)

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": json.dumps(payload, ensure_ascii=True),
                            }
                        ],
                    }
                ],
                temperature=self.TEMPERATURE,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": f"{agent_name}_response",
                        "strict": True,
                        "schema": schema,
                    }
                },
            )

            parsed = self.safe_parse(getattr(response, "output_text", ""))
            if parsed is None:
                raise ValueError("Model returned invalid JSON")

            self._log_usage(agent_name, payload, "success", response, estimated_tokens)
            return parsed
        except Exception as exc:  # pragma: no cover - runtime safety
            self.disabled_reason = str(exc)
            self.client = None
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

    @staticmethod
    def _schema_for_agent(agent_name: str) -> Dict[str, Any]:
        if agent_name == "triage":
            return {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "dashboard_title": {"type": "string"},
                    "operator_summary": {"type": "string"},
                    "risk_explanation": {"type": "string"},
                    "recommended_priority": {"type": "string"},
                    "tts_message": {"type": "string"},
                    "requires_operator_review": {"type": "boolean"},
                },
                "required": [
                    "dashboard_title",
                    "operator_summary",
                    "risk_explanation",
                    "recommended_priority",
                    "tts_message",
                    "requires_operator_review",
                ],
            }

        if agent_name == "timeline":
            return {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "incident_title": {"type": "string"},
                    "timeline_summary": {"type": "string"},
                    "recommended_next_step": {"type": "string"},
                },
                "required": ["incident_title", "timeline_summary", "recommended_next_step"],
            }

        if agent_name == "actions":
            return {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "action_plan": {"type": "array", "items": {"type": "string"}},
                    "operator_note": {"type": "string"},
                    "escalation_hint": {"type": "string"},
                },
                "required": ["action_plan", "operator_note", "escalation_hint"],
            }

        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        }
