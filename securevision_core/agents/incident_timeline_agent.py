import time
import uuid
from typing import Any, Dict, Optional

from agents.slm_service import SLMService


class IncidentTimelineAgent:
    WINDOW_SECONDS = 120.0

    def __init__(self, slm_service: SLMService) -> None:
        self.slm_service = slm_service
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def update_incident(self, payload: Dict[str, Any], use_model: bool = False) -> Dict[str, Any]:
        incident = self._find_existing_incident(payload)
        now = time.time()
        incident_update = False

        if incident is None:
            incident = {
                "incident_id": f"inc_{uuid.uuid4().hex[:10]}",
                "group_key": self._group_key(payload),
                "event_type": payload.get("event_type"),
                "camera_id": payload.get("camera_id"),
                "camera_name": payload.get("camera_name"),
                "sector": payload.get("sector"),
                "area": payload.get("area"),
                "first_seen": now,
                "last_seen": now,
                "detections_count": 1,
                "max_confidence": float(payload.get("confidence") or 0.0),
                "evidence_count": int(payload.get("evidence_increment", 0) or 0),
            }
            self.incidents[incident["incident_id"]] = incident
        else:
            incident_update = True
            incident["last_seen"] = now
            incident["detections_count"] += 1
            incident["max_confidence"] = max(
                float(incident.get("max_confidence", 0.0) or 0.0),
                float(payload.get("confidence") or 0.0),
            )
            incident["evidence_count"] += int(payload.get("evidence_increment", 0) or 0)

        model_payload = {
            "event_type": incident.get("event_type"),
            "camera_id": incident.get("camera_id"),
            "camera_name": incident.get("camera_name"),
            "sector": incident.get("sector"),
            "area": incident.get("area"),
            "first_seen": incident.get("first_seen"),
            "last_seen": incident.get("last_seen"),
            "detections_count": incident.get("detections_count"),
            "max_confidence": incident.get("max_confidence"),
            "evidence_count": incident.get("evidence_count"),
            "incident_update": incident_update,
        }

        if use_model:
            system_prompt = (
                "You are the SecureVision Incident Timeline Agent. "
                "Return STRICT JSON only. Summarize the evolving incident without changing event facts. "
                "Produce an incident_title, a brief timeline_summary, and a recommended_next_step."
            )
            llm_summary = self.slm_service.generate_json(system_prompt, model_payload, "timeline")
        else:
            llm_summary = self.slm_service.fallback_response("timeline", model_payload)

        incident["incident_title"] = llm_summary.get("incident_title", incident.get("incident_title"))
        incident["timeline_summary"] = llm_summary.get("timeline_summary", "")
        incident["recommended_next_step"] = llm_summary.get("recommended_next_step", "")

        return {
            "incident_id": incident["incident_id"],
            "event_type": incident.get("event_type"),
            "camera_id": incident.get("camera_id"),
            "camera_name": incident.get("camera_name"),
            "sector": incident.get("sector"),
            "area": incident.get("area"),
            "first_seen": incident.get("first_seen"),
            "last_seen": incident.get("last_seen"),
            "detections_count": incident.get("detections_count"),
            "max_confidence": incident.get("max_confidence"),
            "evidence_count": incident.get("evidence_count"),
            "incident_title": incident.get("incident_title"),
            "timeline_summary": incident.get("timeline_summary"),
            "recommended_next_step": incident.get("recommended_next_step"),
            "is_update": incident_update,
        }

    def will_update(self, payload: Dict[str, Any]) -> bool:
        return self._find_existing_incident(payload) is not None

    def _find_existing_incident(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = time.time()
        group_key = self._group_key(payload)
        for incident in self.incidents.values():
            if incident.get("group_key") != group_key:
                continue
            if now - float(incident.get("last_seen", 0) or 0) <= self.WINDOW_SECONDS:
                return incident
        return None

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
