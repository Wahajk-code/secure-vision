from typing import Any, Dict

from agents.slm_service import SLMService


class AlertTriageAgent:
    def __init__(self, slm_service: SLMService) -> None:
        self.slm_service = slm_service

    def triage(self, payload: Dict[str, Any], use_model: bool = False) -> Dict[str, Any]:
        enriched_payload = {
            "event_type": payload.get("event_type"),
            "severity": payload.get("severity"),
            "risk_score": payload.get("risk_score"),
            "camera_id": payload.get("camera_id"),
            "camera_name": payload.get("camera_name"),
            "sector": payload.get("sector"),
            "area": payload.get("area"),
            "confidence": payload.get("confidence"),
            "status": payload.get("status"),
        }

        if not use_model:
            return self.slm_service.fallback_response("triage", enriched_payload)

        system_prompt = (
            "You are the SecureVision Alert Triage Agent. "
            "Return STRICT JSON only. Never change severity, event_type, or risk_score. "
            "Explain the alert in short, operator-facing language. "
            "recommended_priority should be a short label such as IMMEDIATE, HIGH, or STANDARD."
        )
        response = self.slm_service.generate_json(system_prompt, enriched_payload, "triage")
        response["severity"] = payload.get("severity")
        return response
