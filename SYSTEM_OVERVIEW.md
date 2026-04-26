# SecureVision System Overview

## 1. Overview
SecureVision is a real-time surveillance platform that detects and operationalizes three security incident types:

- weapons
- physical fights
- abandoned luggage

The current system is built around:

- a Python AI/runtime backend in `securevision_core`
- a React/TypeScript operations dashboard in `securevision_frontend`
- PostgreSQL event storage for history and analytics
- a deterministic alert rules layer for severity, risk score, and spoken alerts
- an OpenAI-backed agentic layer for operator summaries, incident timelines, and action plans

Core system rules remain the source of truth. The OpenAI layer is used only for explanation, summaries, and operator guidance.

## 2. Current Runtime Architecture

### 2.1 Active Backend Path
The active backend/runtime path is:

- `securevision_core/run_system.py`
- `securevision_core/api/main.py`
- `securevision_core/core_pipeline/pipeline.py`

`run_system.py` is the primary entrypoint. It:

- starts FastAPI on port `8001`
- loads a mixed local video playlist from `securevision_core/testvideos`
- assigns each video to a logical camera ID
- reads frames in a background reader thread
- runs the AI pipeline on resized frames
- normalizes detections into rule-based operational alerts
- queues TTS when allowed by cooldown logic
- submits critical/qualified incidents to the agentic layer
- uploads critical evidence frames to Cloudinary
- broadcasts live data to the React dashboard over WebSockets
- shows a native OpenCV monitoring window

### 2.2 Active Frontend Path
The active dashboard is the React app in `securevision_frontend`. It provides:

- login and signup
- JWT-based protected access
- a live target table
- active critical incidents
- agentic alert and operator action cards
- analytics based on database history
- critical evidence/screenshot review
- camera, sector, and area settings
- account deletion and logout flows

### 2.3 Legacy UI Path
`securevision_core/main.py` and `securevision_core/ui/` still contain a Streamlit-based legacy UI path. It is not the main runtime used by the React/FastAPI stack.

## 3. End-to-End Flow

### 3.1 Frame Ingestion
`run_system.py` uses `VideoReaderThread` to continuously decode a playlist of local test videos. Each playlist item is mapped to a logical camera such as `cam_01` through `cam_04`.

The reader thread:

- decodes frames continuously
- buffers frames in an in-memory queue
- emits `VIDEO_RESET` when the playlist advances

### 3.2 Per-Frame Processing
For each frame:

1. the frame is converted from BGR to RGB
2. the frame is resized to `PROCESSING_WIDTH` while preserving aspect ratio
3. `SecureVisionPipeline.process_frame(...)` is called

### 3.3 Detection and Tracking
Inside `core_pipeline/pipeline.py`:

1. `real_layer1.get_yolo_detections(...)` runs two Ultralytics YOLO models sequentially
2. the base model detects `person`, `backpack`, `handbag`, and `suitcase`
3. the weapon model detects `Gun`, `gun`, and `rifle`
4. both models use `.track(...)` with BoTSORT persistence
5. normalized detections include:
   - `track_id`
   - `class`
   - `bbox`
   - `centroid`
   - `confidence`
6. `TrackerState.update(...)` stores bbox/centroid history and owner state

### 3.4 Fight Detection
Fight detection is handled by `core_pipeline/fight_detector.py`, not `layer2_logic.py`.

The current fight path combines:

- person-pair proximity checks
- body/centroid velocity heuristics
- per-person pose estimation on ROI crops via `pose26n.pt`
- arm/contact activity scoring from `pose_filter.py`
- sequence confirmation through `fightnet_integration.py`

Fight states surfaced by the runtime include warning/high-activity and confirmed critical fight states.

### 3.5 Re-Identification
`core_pipeline/reid_manager.py` uses MobileNetV3-based embeddings to create more persistent person identities across tracker churn.

This helps:

- stabilize person identity
- preserve luggage owner continuity
- reduce fragmentation when BoTSORT IDs change

### 3.6 Luggage Ownership and Abandonment
`TrackerState.assign_owners()` associates luggage with the nearest active persistent person.

Current behavior:

- luggage classes are `backpack`, `handbag`, `suitcase`
- luggage warning is delayed until it has been unattended for `LUGGAGE_WARNING_DELAY_FRAMES`
- critical abandoned luggage occurs at `ABANDONED_DURATION_FRAMES`
- ghost tracks are kept for luggage/person classes to reduce false alarms from brief occlusion

### 3.7 Deterministic Alert Layer
Pipeline objects are converted into normalized events by:

- `agents/event_normalizer.py`

Those normalized events are then evaluated by:

- `agents/alert_rules.py`

This rule layer is the source of truth for:

- `event_type`
- `subtype`
- `severity`
- `risk_level`
- `score`
- `recommended_action`
- `dashboard_message`
- `spoken_message`
- whether an alert should be spoken

### 3.8 Agentic Operations Layer
After rule evaluation, `run_system.py` submits qualifying incidents to:

- `agents/operations_agent_layer.py`

That orchestration layer runs:

1. `AlertTriageAgent`
2. `IncidentTimelineAgent`
3. `OperatorActionAgent`

OpenAI is used only for:

- dashboard/operator summaries
- incident titles and timeline summaries
- operator action plans and escalation hints

OpenAI does not override severity, event type, risk score, or the core alert decision.

### 3.9 Broadcasting
`api/main.py` exposes:

- `ws://localhost:8001/ws/stats`

The backend broadcasts:

- `LIVE_FEED`
- `WARNING`
- `CRITICAL`
- `AGENTIC_ALERT`
- `CRITICAL_IMAGE`
- periodic FPS/info logs

### 3.10 Evidence Capture
Critical events can trigger evidence capture and async upload through:

- `utils/cloudinary_helper.py`

Critical image broadcasts include metadata such as:

- `camera_id`
- `camera_name`
- `sector`
- `area`
- `stream_id`

### 3.11 Historical Storage
`utils/stats_manager.py` logs events to PostgreSQL.

Stored event details are enriched through the alert rule engine so analytics and summaries can reuse:

- severity
- risk score
- location metadata
- spoken message
- recommended action

### 3.12 Daily Summaries
`agents/summary_agent.py` generates a daily operational summary from stored events.

## 4. Current Specifications

### 4.1 Threat Classes
Current detection focus:

- weapons: `Gun`, `gun`, `rifle`
- people: `person`
- luggage: `backpack`, `handbag`, `suitcase`

Notes:

- `knife` still appears in confidence and alert logic, but it is not currently in `WEAPON_CLASSES`
- weapon detection is split across a base model and a dedicated weapon model

### 4.2 Current Thresholds
Current values in `securevision_core/config.py`:

- `FRAME_RATE = 30`
- `PROCESSING_WIDTH = 640`
- `PROXIMITY_THRESHOLD_METERS = 1.0`
- `SUSTAINED_DURATION_FRAMES = 60`
- `WEAPON_CONFIRMATION_FRAMES = 15`
- `ABANDONED_DURATION_FRAMES = 300`
- `LUGGAGE_WARNING_DELAY_FRAMES = 90`
- `LUGGAGE_PROXIMITY_THRESHOLD = 200`
- `GHOST_FRAMES_WEAPON = 0`
- `GHOST_FRAMES_LUGGAGE = 30`
- `GHOST_FRAMES_PERSON = 15`
- `MIN_CONFIDENCE = 0.15`

Internal fight detector thresholds currently include:

- proximity threshold: `150` pixels
- sustained activity velocity threshold: `2.0`
- explosive movement threshold: `5.0`
- pose activity threshold: `90.0`

### 4.3 Camera Model
Camera definitions are managed by `utils/camera_registry.py`.

Stored camera fields:

- `id`
- `name`
- `sector`
- `area`
- `is_active`

Camera assignments are persisted in:

- `securevision_core/camera_config.json`

### 4.4 Auth
Authentication uses:

- FastAPI auth routes
- SQLAlchemy `users` table
- JWT bearer tokens
- Passlib password hashing

Current auth endpoints:

- `POST /auth/login`
- `POST /auth/signup`
- `DELETE /users/me`

## 5. Backend Modules

### 5.1 `securevision_core/api`
- `main.py`: FastAPI app, WebSocket broadcaster, stats API, camera API, summary API
- `auth.py`: login and signup routes
- `users.py`: authenticated self-delete route

### 5.2 `securevision_core/core_pipeline`
- `pipeline.py`: orchestrates detections, tracking, fight/luggage logic, drawing, logging hooks
- `real_layer1.py`: loads YOLO models and runs tracking inference
- `tracker_state.py`: track history, persistent person mapping, luggage ownership
- `fight_detector.py`: active fight detection path
- `fightnet_integration.py`: FightNet reconstruction/inference
- `pose_filter.py`: pose ROI inference and arm/contact activity scoring
- `reid_manager.py`: person re-identification
- `layer2_logic.py`: older alternate fight-logic file; not used by the integrated pipeline

### 5.3 `securevision_core/agents`
- `alert_rules.py`: deterministic alert scoring and messaging
- `event_normalizer.py`: pipeline object normalization
- `tts_agent.py`: cooldown-aware non-blocking spoken alert queue
- `summary_agent.py`: daily summary generation
- `slm_service.py`: strict-JSON OpenAI wrapper with fallback logic
- `alert_triage_agent.py`: operator-facing triage summaries
- `incident_timeline_agent.py`: in-memory incident grouping and timeline summaries
- `operator_action_agent.py`: rule-based templates plus contextual operator guidance
- `operations_agent_layer.py`: agentic orchestration layer

### 5.4 `securevision_core/utils`
- `stats_manager.py`: PostgreSQL logging and retrieval
- `camera_registry.py`: camera metadata persistence
- `cloudinary_helper.py`: evidence upload and post-upload broadcast
- `logger.py`: file/console logging

## 6. Frontend Modules

### 6.1 Routing and Auth
- `src/App.tsx`
- `src/context/AuthContext.tsx`
- `src/pages/Login.tsx`
- `src/pages/Signup.tsx`
- `src/pages/Settings.tsx`

### 6.2 Dashboard and Incident UI
- `src/layouts/DashboardLayout.tsx`
- `src/components/LiveEventsTable.tsx`
- `src/components/StatsPanel.tsx`
- `src/components/AgenticAlertCard.tsx`
- `src/components/ActiveIncidentsPanel.tsx`
- `src/components/OperatorActionCard.tsx`
- `src/components/IncidentDetailModal.tsx`
- `src/components/Toast.tsx`
- `src/components/AnalyticsPanel.tsx`
- `src/components/DatabaseView.tsx`
- `src/components/Sidebar.tsx`

## 7. Interfaces

### 7.1 WebSocket
- `GET ws://localhost:8001/ws/stats`

Used for:

- live tracked objects
- warning and critical alerts
- agentic alerts
- FPS/info logs
- critical image updates

### 7.2 REST
- `GET /api/stats`
- `GET /api/summary/daily`
- `GET /api/cameras`
- `PUT /api/cameras`
- `POST /auth/login`
- `POST /auth/signup`
- `DELETE /users/me`

## 8. Database Design
The project uses PostgreSQL in two ways:

- SQLAlchemy ORM for user accounts
- Psycopg2/raw SQL for security event logging

Primary tables:

- `users`
- `security_events`

`security_events` stores:

- unix timestamp
- datetime
- event type
- JSON details
- stream ID

The `details` payload can contain enriched alert metadata such as:

- subtype
- severity
- risk level
- score
- location metadata
- dashboard/spoken messages
- recommended action

## 9. Models and Dependencies

### 9.1 Active Models
The active code path references:

- `models/yolo11n.pt`
- `models/weapon_detection4.pt`
- `models/pose26n.pt`
- `models/fightnet_best_model.pt`

### 9.2 Backend Dependencies
Important backend packages include:

- `fastapi`
- `uvicorn`
- `opencv-python`
- `numpy`
- `ultralytics`
- `torch`
- `torchvision`
- `psycopg2-binary`
- `sqlalchemy`
- `python-jose`
- `passlib`
- `pyttsx3`
- `cloudinary`
- `openai`
- `streamlit` for the legacy UI path

### 9.3 Frontend Dependencies
Important frontend packages include:

- `react`
- `typescript`
- `vite`
- `react-router-dom`
- `recharts`
- `lucide-react`
- `tailwindcss`

## 10. Current Operational Behavior

### 10.1 Weapon Detection
- both YOLO models run each frame
- weapons are filtered by class-specific confidence thresholds
- overly large weapon boxes are rejected with area/height/width ratio checks
- a person must be present for a weapon to be operationally flagged
- warnings can be used during frame confirmation
- confirmed weapons require `WEAPON_CONFIRMATION_FRAMES`
- critical weapon events can trigger evidence upload and speech

### 10.2 Fight Detection
- only nearby person pairs are considered
- body velocity is measured from track history
- pose verification is only run on suspicious pairs
- pose activity is buffered over time
- FightNet confirms the sequence
- warnings and critical fight states are separated
- warning and critical fight speech use cooldown rules

### 10.3 Abandoned Luggage
- luggage is associated to the nearest persistent person
- warning is delayed until the unattended timer passes `LUGGAGE_WARNING_DELAY_FRAMES`
- critical is raised at `ABANDONED_DURATION_FRAMES`
- warning and critical luggage speech use cooldown rules
- confirmed critical luggage can trigger evidence capture

## 11. Important Implementation Notes

- `layer2_logic.py` exists but is not the active fight path.
- `VideoFeed.tsx` is not part of the current dashboard flow and still points to an older MJPEG endpoint on port `8000`.
- `securevision_core/main.py` and `securevision_core/ui/` represent a legacy Streamlit path.
- `api/main.py` currently provides the WebSocket/REST API, but it still contains some older duplicate/comment-heavy scaffolding that is a cleanup candidate.
- the OpenAI/SLM layer is designed with strict JSON responses and deterministic fallbacks
- OpenAI calls are cost-controlled and not run per frame

## 12. Recommended Startup Path

1. Start PostgreSQL and ensure `security_events` exists.
2. Ensure required model files are present under `securevision_core/models`.
3. Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL=gpt-4o-mini`.
4. Run `securevision_core/run_system.py`.
5. Run the React frontend in `securevision_frontend`.
6. Open the dashboard and connect to `ws://localhost:8001/ws/stats`.

This path provides:

- live AI processing
- deterministic operational alerts
- agentic summaries and operator guidance
- database-backed analytics
- evidence uploads
- configurable camera metadata
- spoken alerts with cooldown control
