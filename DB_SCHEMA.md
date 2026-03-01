# SecureVision Database Schema

The system uses **PostgreSQL** as the primary data store. The schema is hybrid, using both **SQLAlchemy ORM** (for Users) and **Raw SQL** (for High-Frequency Events).

---

## 1. Users Table (`users`)
**Managed By**: SQLAlchemy ORM
**File**: `securevision_core/models_db.py`
**Purpose**: Authentication and Authorization.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | Auto-incrementing unique ID. |
| `username` | `VARCHAR` | `UNIQUE`, `INDEX` | Login username. |
| `hashed_password` | `VARCHAR` | | Bcrypt hashed password. |
| `role` | `VARCHAR` | `DEFAULT 'admin'` | RBAC role (admin/operator). |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | Soft deletion flag. |

```python
# Model Definition
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    # ...
```

---

## 2. Security Events Table (`security_events`)
**Managed By**: Raw SQL (Psycopg2)
**File**: `securevision_core/verify_db.py`, `securevision_core/utils/stats_manager.py`
**Purpose**: Immutable log of all detected threats (Weapons, Fights, Abandoned Luggage).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | Auto-incrementing Log ID. |
| `timestamp` | `FLOAT` | | Unix timestamp (Epoch). |
| `datetime` | `TIMESTAMP` | | Human-readable ISO 8601 date. |
| `event_type` | `VARCHAR(50)` | | e.g. `WEAPON`, `FIGHT`, `ABANDONED_LUGGAGE`. |
| `details` | `JSONB` | | Flexible storage for metadata (track IDs, confidence). |
| `stream_id` | `VARCHAR(100)` | | Originating camera/stream identifier. |

**SQL Definition**:
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

---

## 3. Database Initialization
-   **Users**: Initialized via `securevision_core/seed.py` (Creates admin user `wahaj/wahaj123` if missing).
-   **Events**: Initialized via `securevision_core/verify_db.py`.
