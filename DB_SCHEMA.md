# SecureVision Database Schema

SecureVision currently uses PostgreSQL in two different ways:

- SQLAlchemy ORM for user accounts
- Psycopg2/raw SQL for high-frequency security event logging

## 1. Users Table
**Managed by**: SQLAlchemy ORM  
**Source file**: `securevision_core/models_db.py`

The `users` table stores operator/admin authentication data.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY`, `INDEX` | Auto-incrementing user ID |
| `username` | `VARCHAR` | `UNIQUE`, `INDEX` | Login username |
| `hashed_password` | `VARCHAR` | | Password hash |
| `role` | `VARCHAR` | `DEFAULT 'admin'` | User role |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | Active account flag |

Current ORM model:

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="admin")
    is_active = Column(Boolean, default=True)
```

## 2. Security Events Table
**Managed by**: Raw SQL via `securevision_core/utils/stats_manager.py`  
**Creation helper**: `securevision_core/verify_db.py`

The `security_events` table stores historical security incidents.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | Auto-incrementing event ID |
| `timestamp` | `FLOAT` | | Unix timestamp |
| `datetime` | `TIMESTAMP` | | Human-readable event time |
| `event_type` | `VARCHAR(50)` | | `WEAPON`, `FIGHT`, `ABANDONED_LUGGAGE`, etc. |
| `details` | `JSONB` | | Enriched event metadata |
| `stream_id` | `VARCHAR(100)` | | Source stream/camera identifier |

Current SQL definition:

```sql
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    timestamp FLOAT,
    datetime TIMESTAMP,
    event_type VARCHAR(50),
    details JSONB,
    stream_id VARCHAR(100)
);
```

## 3. What `details` Contains
`details` is not just raw detector output. Before insertion, `StatsManager` enriches the payload through the rule engine so the database stores operator-ready context.

Typical fields may include:

- `event_type`
- `subtype`
- `severity`
- `risk_level`
- `score`
- `status`
- `camera_id`
- `camera_name`
- `sector`
- `area`
- `dashboard_message`
- `spoken_message`
- `recommended_action`
- `priority`
- detector-specific fields such as `frames_seen`, `confidence`, `track_id`, `pose`, `velocity`, `timer`

The exact contents vary by incident type.

## 4. Event Enrichment Rules
`securevision_core/utils/stats_manager.py` currently applies deterministic enrichment before storage:

- `WEAPON`
  - normalizes subtype from the detected class
  - defaults `frames_seen` to `WEAPON_CONFIRMATION_FRAMES` if needed
- `FIGHT`
  - forces subtype to `physical_altercation`
  - defaults status to `CONFIRMED`
- `ABANDONED_LUGGAGE`
  - forces subtype to `luggage`
  - defaults status to `CRITICAL`

It then resolves camera metadata from `camera_registry.py` and passes the event through `AlertRuleEngine` so the stored payload reflects the same operational interpretation seen by the dashboard.

## 5. Read Path
Historical events are returned by:

- `GET /api/stats`

The current response shape is:

```json
{
  "events": [
    {
      "timestamp": 1710000000.0,
      "datetime": "2026-04-26T18:00:00",
      "type": "WEAPON",
      "details": {},
      "stream_id": "desktop_stream_cam_01"
    }
  ]
}
```

## 6. Initialization Notes
- `users` are created through SQLAlchemy table creation and auth flows
- `security_events` can be ensured by `verify_db.py`
- `run_system.py` and `StatsManager` assume PostgreSQL is already available

## 7. Current Design Notes
- the database stores immutable event history rather than updating a live incident row
- incident grouping for the dashboard is currently in-memory inside `IncidentTimelineAgent`
- there is no dedicated `incidents` table yet
- operator-facing agentic outputs are broadcast live and are not currently persisted as a separate table
