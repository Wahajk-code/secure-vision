import json
import time
from datetime import datetime
import psycopg2
from config import DB_CONFIG

class StatsManager:
    def __init__(self):
        pass # No file init needed

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
                json.dumps(details or {}),
                stream_id
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error logging stats to DB: {e}")

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
