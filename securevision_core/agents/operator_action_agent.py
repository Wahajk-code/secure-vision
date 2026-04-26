from typing import Any, Dict, List

from agents.slm_service import SLMService


class OperatorActionAgent:
    def __init__(self, slm_service: SLMService) -> None:
        self.slm_service = slm_service

    def build_actions(
        self,
        payload: Dict[str, Any],
        triage: Dict[str, Any] | None = None,
        incident: Dict[str, Any] | None = None,
        use_model: bool = False,
    ) -> Dict[str, Any]:
        base_actions = self._base_actions(str(payload.get("event_type", "UNKNOWN")).upper())
        action_payload = {
            "event_type": payload.get("event_type"),
            "subtype": payload.get("subtype"),
            "severity": payload.get("severity"),
            "risk_level": payload.get("risk_level"),
            "risk_score": payload.get("risk_score"),
            "status": payload.get("status"),
            "confidence": payload.get("confidence"),
            "camera_id": payload.get("camera_id"),
            "camera_name": payload.get("camera_name"),
            "sector": payload.get("sector"),
            "area": payload.get("area"),
            "recommended_action": payload.get("recommended_action"),
            "dashboard_message": payload.get("dashboard_message"),
            "base_actions": base_actions,
            "triage_context": {
                "dashboard_title": (triage or {}).get("dashboard_title"),
                "operator_summary": (triage or {}).get("operator_summary"),
                "risk_explanation": (triage or {}).get("risk_explanation"),
                "recommended_priority": (triage or {}).get("recommended_priority"),
            },
            "incident_context": {
                "incident_id": (incident or {}).get("incident_id"),
                "incident_title": (incident or {}).get("incident_title"),
                "timeline_summary": (incident or {}).get("timeline_summary"),
                "recommended_next_step": (incident or {}).get("recommended_next_step"),
                "detections_count": (incident or {}).get("detections_count"),
                "evidence_count": (incident or {}).get("evidence_count"),
            },
        }

        if not use_model:
            return self.slm_service.fallback_response("actions", action_payload)

        system_prompt = (
            "You are the SecureVision Operator Action Agent. "
            "Return STRICT JSON only. Do not change severity, event_type, or risk_score. "
            "Use the provided location, subtype, rule-based recommendation, triage summary, and incident timeline to "
            "personalize the action plan for the operator. "
            "Keep the action_plan in the same order as base_actions, but rewrite each step into clear, location-aware "
            "instructions for this specific incident. "
            "operator_note should be a short situational note grounded in the current context. "
            "escalation_hint should state when and why the operator should escalate next."
        )
        response = self.slm_service.generate_json(system_prompt, action_payload, "actions")
        if not response.get("action_plan"):
            response["action_plan"] = base_actions
        return response

    @staticmethod
    def _base_actions(event_type: str) -> List[str]:
        if event_type == "WEAPON":
            return ["Focus camera on suspect", "Dispatch nearest guard", "Preserve evidence footage"]
        if event_type == "FIGHT":
            return ["Dispatch nearest guard", "Monitor involved individuals", "Confirm scene resolution"]
        if event_type == "ABANDONED_LUGGAGE":
            return ["Inspect item from a safe distance", "Monitor surrounding area", "Escalate if unattended status persists"]
        return ["Monitor scene", "Review system details", "Escalate if needed"]
