import re
import time
from typing import Any, Dict
from config import WEAPON_CONFIRMATION_FRAMES


def normalize_pipeline_item(item: Dict[str, Any], stream_id: str = "desktop_stream", camera: Dict[str, Any] = None) -> Dict[str, Any]:
    category = str(item.get("category", "")).strip()
    status = str(item.get("status", "")).strip()
    details = str(item.get("details", "")).strip()
    lower_category = category.lower()
    upper_details = details.upper()

    event_type = "UNKNOWN"
    subtype = lower_category or "unknown"

    if lower_category in {"gun", "rifle", "knife", "pistol"}:
        event_type = "WEAPON"
    elif lower_category in {"luggage", "backpack", "handbag", "suitcase"}:
        event_type = "ABANDONED_LUGGAGE"
        subtype = "luggage" if lower_category == "luggage" else lower_category
    elif lower_category == "person" and ("FIGHTING" in upper_details or "ANALYZING" in upper_details):
        event_type = "FIGHT"
        subtype = "physical_altercation"

    event = {
        "event_type": event_type,
        "subtype": subtype,
        "track_id": item.get("id"),
        "category": category,
        "status": status,
        "details": details,
        "confidence": item.get("confidence"),
        "stream": stream_id,
        "timestamp": time.strftime("%H:%M:%S"),
    }

    if camera:
        event.update({
            "camera_id": camera.get("id"),
            "camera_name": camera.get("name"),
            "sector": camera.get("sector"),
            "area": camera.get("area"),
        })

    if event_type == "WEAPON":
        match = re.search(r"\((\d+)/(\d+)\)", details)
        if match:
            event["frames_seen"] = int(match.group(1))
        elif status.upper() == "CRITICAL":
            event["frames_seen"] = WEAPON_CONFIRMATION_FRAMES

    if event_type == "FIGHT":
        velocity = re.search(r"V:([0-9.]+)", details)
        pose = re.search(r"P:([0-9.]+)", details)
        timer = re.search(r"(?:Analyzing|Wait:)\s*([0-9]+)", details)
        if velocity:
            event["velocity"] = float(velocity.group(1))
        if pose:
            event["pose"] = float(pose.group(1))
        if timer:
            event["timer"] = int(timer.group(1))

    return event
