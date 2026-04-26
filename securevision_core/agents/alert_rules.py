from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from config import WEAPON_CONFIRMATION_FRAMES


@dataclass
class AlertDecision:
    event_type: str
    subtype: str
    severity: str
    risk_level: str
    priority: int
    score: int
    status: str
    dashboard_message: str
    spoken_message: str
    recommended_action: str
    should_alert: bool = True
    should_speak: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_websocket_payload(self) -> Dict[str, Any]:
        return {
            "type": self.severity,
            "message": self.dashboard_message,
            "timestamp": self.metadata.get("timestamp"),
            "event_type": self.event_type,
            "subtype": self.subtype,
            "severity": self.severity,
            "risk_level": self.risk_level,
            "priority": self.priority,
            "score": self.score,
            "recommended_action": self.recommended_action,
            "spoken_message": self.spoken_message,
            "metadata": self.metadata,
        }

    def to_db_details(self) -> Dict[str, Any]:
        details = dict(self.metadata)
        details.update({
            "subtype": self.subtype,
            "severity": self.severity,
            "risk_level": self.risk_level,
            "priority": self.priority,
            "score": self.score,
            "status": self.status,
            "dashboard_message": self.dashboard_message,
            "spoken_message": self.spoken_message,
            "recommended_action": self.recommended_action,
        })
        return details


class AlertRuleEngine:
    """Deterministic, auditable alert rules for immediate security decisions."""

    WEAPON_PRIORITY = {
        "rifle": 1,
        "gun": 1,
        "firearm": 1,
        "pistol": 1,
        "knife": 2,
    }

    def evaluate(self, event: Dict[str, Any]) -> AlertDecision:
        event_type = str(event.get("event_type", "UNKNOWN")).upper()
        if event_type == "WEAPON":
            return self._evaluate_weapon(event)
        if event_type == "FIGHT":
            return self._evaluate_fight(event)
        if event_type == "ABANDONED_LUGGAGE":
            return self._evaluate_luggage(event)
        return self._evaluate_unknown(event)

    def _evaluate_weapon(self, event: Dict[str, Any]) -> AlertDecision:
        subtype = str(event.get("subtype") or event.get("class") or "weapon").lower()
        frames_seen = int(event.get("frames_seen", WEAPON_CONFIRMATION_FRAMES) or 0)
        confidence = float(event.get("confidence", 0.0) or 0.0)
        person_present = bool(event.get("person_present", True))
        location = self._format_location(event)

        base = 95 if subtype == "rifle" else 90 if subtype in {"gun", "pistol", "firearm"} else 85
        if confidence >= 0.70:
            base += 5
        if not person_present:
            base -= 25

        required_frames = 8 if subtype == "knife" else WEAPON_CONFIRMATION_FRAMES
        if frames_seen < required_frames:
            score = max(55, base - 30)
            severity = "WARNING"
            status = "VERIFYING"
            risk_level = "MEDIUM"
            should_speak = False
            action = "Keep camera locked on target and verify the object before escalation."
            dashboard = f"Possible {subtype} detected at {location}. Verifying weapon evidence."
            spoken = f"Possible {subtype} at {location}. Verify target."
        else:
            score = min(100, base)
            severity = "CRITICAL"
            status = "CONFIRMED"
            risk_level = "HIGH"
            should_speak = True
            if subtype in {"gun", "pistol", "firearm", "rifle"}:
                action = "Initiate lockdown, notify the response team, contact police, and move civilians away from the area."
                spoken = f"Critical firearm at {location}. Lock down and dispatch response."
            else:
                action = "Isolate the area, dispatch trained security, track suspect movement, and prepare medical support."
                spoken = f"Critical knife at {location}. Isolate area and dispatch security."
            dashboard = f"{subtype.title()} detected at {location}. High danger. Immediate supervisor response required."

        return AlertDecision(
            event_type="WEAPON",
            subtype=subtype,
            severity=severity,
            risk_level=risk_level,
            priority=self.WEAPON_PRIORITY.get(subtype, 2),
            score=score,
            status=status,
            dashboard_message=dashboard,
            spoken_message=spoken,
            recommended_action=action,
            should_speak=should_speak,
            metadata=event,
        )

    def _evaluate_fight(self, event: Dict[str, Any]) -> AlertDecision:
        velocity = float(event.get("velocity", 0.0) or 0.0)
        pose = float(event.get("pose", 0.0) or 0.0)
        timer = int(event.get("timer", 0) or 0)
        confirmed = str(event.get("status", "")).upper() in {"CRITICAL", "CONFIRMED"}
        location = self._format_location(event)

        score = 25
        if timer >= 15:
            score += 15
        if timer >= 30:
            score += 10
        if velocity >= 2.0:
            score += 20
        if velocity >= 5.0:
            score += 10
        if pose >= 90.0:
            score += 20
        if confirmed:
            score += 20
        score = min(score, 100)

        if score >= 90 or confirmed:
            severity = "CRITICAL"
            risk_level = "HIGH"
            status = "CONFIRMED"
            priority = 3
            action = "Dispatch security immediately, separate individuals only if safe, prepare medical assistance, and preserve evidence footage."
            dashboard = f"Fight detected at {location}. Dispatch security and prepare medical support."
            spoken = f"Critical fight at {location}. Dispatch security and medical support."
            should_speak = True
        elif score >= 65:
            severity = "WARNING"
            risk_level = "MEDIUM"
            status = "HIGH_ACTIVITY"
            priority = 5
            action = "Send nearest guard for visual confirmation and continue camera tracking."
            dashboard = f"Possible fight behavior detected at {location}. Supervisor verification recommended."
            spoken = f"Possible fight at {location}. Verify scene."
            should_speak = True
        else:
            severity = "INFO"
            risk_level = "LOW"
            status = "WATCH"
            priority = 9
            action = "Continue monitoring."
            dashboard = "Close interaction detected. Monitoring for escalation."
            spoken = "Close interaction detected."
            should_speak = False

        return AlertDecision(
            event_type="FIGHT",
            subtype="physical_altercation",
            severity=severity,
            risk_level=risk_level,
            priority=priority,
            score=score,
            status=status,
            dashboard_message=dashboard,
            spoken_message=spoken,
            recommended_action=action,
            should_alert=severity != "INFO",
            should_speak=should_speak,
            metadata=event,
        )

    def _evaluate_luggage(self, event: Dict[str, Any]) -> AlertDecision:
        status = str(event.get("status", "")).upper()
        details = str(event.get("details", ""))
        seconds_left = self._extract_seconds_left(details)
        location = self._format_location(event)

        if status == "CRITICAL" or "ABANDONED" in details.upper():
            severity = "CRITICAL"
            risk_level = "HIGH"
            priority = 4
            score = 90
            state = "ABANDONED_CONFIRMED"
            action = "Clear the nearby area, do not touch the object, notify the supervisor, and follow suspicious package protocol."
            dashboard = f"Abandoned luggage confirmed at {location}. Clear the area and follow suspicious package protocol."
            spoken = f"Critical abandoned luggage at {location}."
            should_speak = True
        elif seconds_left is not None:
            severity = "WARNING"
            risk_level = "MEDIUM"
            priority = 6
            score = 60
            state = "OWNER_AWAY"
            action = "Ask the nearest guard to verify ownership from a safe distance and continue monitoring."
            dashboard = f"Possible unattended luggage at {location}. Ownership verification recommended."
            spoken = f"Possible unattended luggage at {location}. Verify ownership."
            should_speak = True
        else:
            severity = "INFO"
            risk_level = "LOW"
            priority = 9
            score = 20
            state = "TRACKING"
            action = "Continue monitoring luggage ownership."
            dashboard = "Luggage tracked. Owner association active."
            spoken = "Luggage tracked."
            should_speak = False

        return AlertDecision(
            event_type="ABANDONED_LUGGAGE",
            subtype=str(event.get("subtype", "luggage")).lower(),
            severity=severity,
            risk_level=risk_level,
            priority=priority,
            score=score,
            status=state,
            dashboard_message=dashboard,
            spoken_message=spoken,
            recommended_action=action,
            should_alert=severity != "INFO",
            should_speak=should_speak,
            metadata=event,
        )

    def _evaluate_unknown(self, event: Dict[str, Any]) -> AlertDecision:
        return AlertDecision(
            event_type=str(event.get("event_type", "UNKNOWN")).upper(),
            subtype=str(event.get("subtype", "unknown")),
            severity="INFO",
            risk_level="LOW",
            priority=9,
            score=0,
            status="UNKNOWN",
            dashboard_message="Unclassified event received.",
            spoken_message="Unclassified event received.",
            recommended_action="Review event metadata.",
            should_alert=False,
            should_speak=False,
            metadata=event,
        )

    @staticmethod
    def _extract_seconds_left(details: str) -> Optional[float]:
        marker = "in "
        if marker not in details:
            return None
        try:
            tail = details.split(marker, 1)[1]
            value = tail.split("s", 1)[0].strip()
            return float(value)
        except (IndexError, ValueError):
            return None

    @staticmethod
    def _format_location(event: Dict[str, Any]) -> str:
        camera = event.get("camera_name") or event.get("camera_id") or "Camera 1"
        sector = event.get("sector")
        area = event.get("area")
        parts = [str(camera)]
        if sector:
            parts.append(str(sector))
        if area:
            parts.append(str(area))
        return ", ".join(parts)
