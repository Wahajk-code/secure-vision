import json
import time
from datetime import datetime
import psycopg2
from config import DB_CONFIG
from config import WEAPON_CONFIRMATION_FRAMES
from agents.alert_rules import AlertRuleEngine
from utils.camera_registry import CameraRegistry

class StatsManager:
    def __init__(self):
        self.alert_rules = AlertRuleEngine()
        self.camera_registry = CameraRegistry()

    def _get_connection(self):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except Exception as e:
            print(f"DB Connection Error: {e}")
            return None

    def log_event(self, event_type, details=None):
        """
        Logs an event to the PostgreSQL database.
        
        Args:
            event_type (str): 'WEAPON', 'FIGHT', 'ABANDONED_LUGGAGE'
            details (dict): Optional details like {'class': 'gun', 'track_id': 1}
        """
        details = self._sanitize_for_json(self._enrich_details(event_type, details or {}))
        conn = self._get_connection()
        if not conn: return

        try:
            cur = conn.cursor()
            query = """
                INSERT INTO security_events (timestamp, datetime, event_type, details, stream_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            stream_id = details.get('stream', 'unknown') if details else 'unknown'
            
            cur.execute(query, (
                time.time(),
                datetime.now(),
                event_type,
                json.dumps(details),
                stream_id
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error logging stats to DB: {e}")

    def _sanitize_for_json(self, value):
        """
        Converts numpy / exotic numeric values into plain Python JSON-safe values.
        """
        if isinstance(value, dict):
            return {str(k): self._sanitize_for_json(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._sanitize_for_json(v) for v in value]
        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                pass
        return value

    def _enrich_details(self, event_type, details):
        """
        Stores deterministic alert interpretation with every event so summaries
        can explain both what happened and what the supervisor should do.
        """
        if not isinstance(details, dict):
            return {"raw_details": details}

        normalized = dict(details)
        normalized["event_type"] = event_type
        if event_type == "WEAPON":
            normalized["subtype"] = str(details.get("class", details.get("subtype", "weapon"))).lower()
            normalized.setdefault("frames_seen", WEAPON_CONFIRMATION_FRAMES)
            normalized.setdefault("person_present", True)
        elif event_type == "FIGHT":
            normalized["subtype"] = "physical_altercation"
            normalized.setdefault("status", "CONFIRMED")
        elif event_type == "ABANDONED_LUGGAGE":
            normalized["subtype"] = "luggage"
            normalized.setdefault("status", "CRITICAL")
            normalized.setdefault("details", "ABANDONED")
        else:
            return normalized

        camera_id = normalized.get("camera_id", "cam_01")
        camera = self.camera_registry.get_camera(camera_id)
        normalized.setdefault("camera_id", camera.get("id"))
        normalized.setdefault("camera_name", camera.get("name"))
        normalized.setdefault("sector", camera.get("sector"))
        normalized.setdefault("area", camera.get("area"))

        try:
            decision = self.alert_rules.evaluate(normalized)
            return decision.to_db_details()
        except Exception as e:
            normalized["alert_enrichment_error"] = str(e)
            return normalized

    def get_stats(self):
        """
        Retrieves all events from the database.
        """
        conn = self._get_connection()
        if not conn: return {"events": []}

        try:
            cur = conn.cursor()
            cur.execute("SELECT timestamp, datetime, event_type, details, stream_id FROM security_events ORDER BY datetime DESC LIMIT 1000")
            rows = cur.fetchall()
            
            events = []
            for row in rows:
                events.append({
                    "timestamp": row[0],
                    "datetime": row[1].isoformat(),
                    "type": row[2],
                    "details": row[3], # JSONB is already dict in Python
                    "stream_id": row[4]
                })
            
            cur.close()
            conn.close()
            return {"events": events}
        except Exception as e:
            print(f"Error fetching stats: {e}")
            return {"events": []}
