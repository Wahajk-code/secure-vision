import time
from typing import Any, Dict

from agents.alert_triage_agent import AlertTriageAgent
from agents.incident_timeline_agent import IncidentTimelineAgent
from agents.operator_action_agent import OperatorActionAgent
from agents.slm_service import SLMService


class OperationsAgentLayer:
    """Orchestrates triage, timeline, and operator action enrichment."""
    MODEL_CALL_COOLDOWN_SECONDS = 30.0

    def __init__(self) -> None:
        self.slm_service = SLMService()
        self.triage_agent = AlertTriageAgent(self.slm_service)
        self.timeline_agent = IncidentTimelineAgent(self.slm_service)
        self.action_agent = OperatorActionAgent(self.slm_service)
        self._last_model_call_by_group: Dict[str, float] = {}

    def process_event(self, original_event: Dict[str, Any], decision: Any) -> Dict[str, Any]:
        payload = self._build_payload(original_event, decision)
        incident_update = self.timeline_agent.will_update(payload)
        use_model = self._should_call_openai(payload, incident_update)
        if use_model:
            self._last_model_call_by_group[self._group_key(payload)] = time.time()

        triage = self.triage_agent.triage(payload, use_model=use_model)
        incident = self.timeline_agent.update_incident(payload, use_model=use_model)
        actions = self.action_agent.build_actions(payload, triage=triage, incident=incident, use_model=use_model)

        return {
            "type": "AGENTIC_ALERT",
            "triage": triage,
            "incident": incident,
            "actions": actions,
            "original_event": payload,
        }

    def _should_call_openai(self, payload: Dict[str, Any], incident_update: bool) -> bool:
        severity = str(payload.get("severity", "")).upper()
        risk_level = str(payload.get("risk_level", "")).upper()
        group_key = self._group_key(payload)
        last_model_call = self._last_model_call_by_group.get(group_key, 0.0)
        in_cooldown = (time.time() - last_model_call) < self.MODEL_CALL_COOLDOWN_SECONDS

        if severity == "CRITICAL":
            return not in_cooldown
        if incident_update and risk_level == "HIGH":
            return not in_cooldown
        return False

    @staticmethod
    def _build_payload(original_event: Dict[str, Any], decision: Any) -> Dict[str, Any]:
        return {
            "event_type": str(original_event.get("event_type", "UNKNOWN")).upper(),
            "subtype": str(
                original_event.get("subtype")
                or original_event.get("class")
                or getattr(decision, "subtype", "unknown")
            ).lower(),
            "severity": getattr(decision, "severity", original_event.get("severity", "WARNING")),
            "risk_level": getattr(decision, "risk_level", original_event.get("risk_level", "MEDIUM")),
            "risk_score": int(getattr(decision, "score", original_event.get("score", 0)) or 0),
            "camera_id": original_event.get("camera_id", "cam_01"),
            "camera_name": original_event.get("camera_name"),
            "sector": original_event.get("sector"),
            "area": original_event.get("area"),
            "confidence": original_event.get("confidence"),
            "status": getattr(decision, "status", original_event.get("status")),
            "stream_id": original_event.get("stream"),
            "recommended_action": getattr(decision, "recommended_action", ""),
            "dashboard_message": getattr(decision, "dashboard_message", ""),
            "track_id": original_event.get("track_id"),
        }

    @staticmethod
    def _group_key(payload: Dict[str, Any]) -> str:
        return "|".join(
            [
                str(payload.get("event_type") or "UNKNOWN"),
                str(payload.get("camera_id") or "cam_01"),
                str(payload.get("sector") or ""),
                str(payload.get("area") or ""),
            ]
        )
