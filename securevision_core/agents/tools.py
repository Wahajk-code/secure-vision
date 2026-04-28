from __future__ import annotations

from typing import Any, Dict, List

from utils.camera_registry import CameraRegistry


class AgentContextTools:
    """Deterministic context helpers that back the LangChain intelligence layer."""

    def __init__(self, camera_registry: CameraRegistry | None = None) -> None:
        self.camera_registry = camera_registry or CameraRegistry()

    def get_camera_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        camera_id = str(payload.get("camera_id") or "cam_01")
        camera = self.camera_registry.get_camera(camera_id)
        return {
            "camera_id": camera.get("id", camera_id),
            "camera_name": camera.get("name") or payload.get("camera_name") or camera_id,
            "sector": camera.get("sector") or payload.get("sector") or "",
            "area": camera.get("area") or payload.get("area") or "",
            "is_active": bool(camera.get("is_active", True)),
        }

    @staticmethod
    def get_rule_context(payload: Dict[str, Any]) -> Dict[str, Any]:
        event_type = str(payload.get("event_type", "UNKNOWN")).upper()
        severity = str(payload.get("severity", "WARNING")).upper()
        risk_level = str(payload.get("risk_level", "MEDIUM")).upper()
        risk_score = int(payload.get("risk_score", payload.get("score", 0)) or 0)
        subtype = str(payload.get("subtype") or event_type.lower()).replace("_", " ")
        recommended_action = str(payload.get("recommended_action") or "").strip()
        dashboard_message = str(payload.get("dashboard_message") or "").strip()

        return {
            "event_type": event_type,
            "subtype": subtype,
            "severity": severity,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "recommended_action": recommended_action,
            "dashboard_message": dashboard_message,
            "priority_hint": self_priority_label(severity, risk_score),
            "rule_constraints": [
                "Do not change severity.",
                "Do not change event_type.",
                "Do not change risk_score.",
                "Do not invalidate the deterministic rule decision.",
            ],
        }

    @staticmethod
    def get_incident_context(payload: Dict[str, Any]) -> Dict[str, Any]:
        incident_context = dict(payload.get("incident_context") or {})
        return {
            "incident_id": incident_context.get("incident_id"),
            "incident_title": incident_context.get("incident_title"),
            "timeline_summary": incident_context.get("timeline_summary"),
            "recommended_next_step": incident_context.get("recommended_next_step"),
            "detections_count": int(incident_context.get("detections_count", payload.get("detections_count", 1)) or 1),
            "evidence_count": int(incident_context.get("evidence_count", payload.get("evidence_count", 0)) or 0),
            "first_seen": incident_context.get("first_seen", payload.get("first_seen")),
            "last_seen": incident_context.get("last_seen", payload.get("last_seen")),
            "incident_update": bool(payload.get("incident_update", False)),
        }

    @staticmethod
    def get_operator_constraints(payload: Dict[str, Any]) -> Dict[str, Any]:
        base_actions = payload.get("base_actions") or default_actions(str(payload.get("event_type", "UNKNOWN")).upper())
        return {
            "base_actions": list(base_actions),
            "must_preserve_order": True,
            "style_rules": [
                "Keep operator instructions concrete and short.",
                "Use the actual camera, sector, and area names when available.",
                "Do not invent responders, equipment, or external systems.",
                "Ground recommendations in the provided event and incident context only.",
            ],
        }


def default_actions(event_type: str) -> List[str]:
    if event_type == "WEAPON":
        return ["Focus camera", "Dispatch guard", "Preserve evidence"]
    if event_type == "FIGHT":
        return ["Dispatch guard", "Monitor individuals", "Confirm resolution"]
    if event_type == "ABANDONED_LUGGAGE":
        return ["Inspect item", "Monitor area", "Escalate if needed"]
    return ["Monitor scene", "Review event details", "Escalate if needed"]


def self_priority_label(severity: str, risk_score: int) -> str:
    if severity == "CRITICAL" or risk_score >= 90:
        return "IMMEDIATE"
    if risk_score >= 70:
        return "HIGH"
    return "STANDARD"
