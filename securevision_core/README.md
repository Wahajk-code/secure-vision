# SecureVision Core

`securevision_core` contains the active backend runtime, AI pipeline, alerting logic, database access, and legacy Streamlit UI files.

## Active Runtime
The current integrated runtime path is:

- `run_system.py`
- `api/main.py`
- `core_pipeline/pipeline.py`

`run_system.py` is the recommended entrypoint. It:

- starts FastAPI on port `8001`
- runs the mixed local video playlist
- processes frames through the AI pipeline
- evaluates alerts with deterministic rules
- queues TTS
- submits qualifying incidents to the agentic layer
- uploads critical evidence to Cloudinary
- broadcasts results over `ws://localhost:8001/ws/stats`

## Main Components

### Core Pipeline
- `core_pipeline/real_layer1.py`: YOLO detection/tracking
- `core_pipeline/tracker_state.py`: history and luggage ownership
- `core_pipeline/fight_detector.py`: active fight path
- `core_pipeline/pose_filter.py`: pose ROI verification
- `core_pipeline/fightnet_integration.py`: FightNet confirmation
- `core_pipeline/reid_manager.py`: person re-identification
- `core_pipeline/pipeline.py`: orchestration

### Alerting And Agents
- `agents/event_normalizer.py`: pipeline event normalization
- `agents/alert_rules.py`: deterministic severity, score, and messaging
- `agents/tts_agent.py`: spoken alert queue/cooldowns
- `agents/slm_service.py`: OpenAI strict-JSON wrapper
- `agents/operations_agent_layer.py`: triage/timeline/actions orchestration

### API And Utilities
- `api/main.py`: WebSocket and REST endpoints
- `utils/stats_manager.py`: PostgreSQL event logging
- `utils/camera_registry.py`: camera metadata
- `utils/cloudinary_helper.py`: evidence upload
- `utils/logger.py`: logging

## Important Notes
- the active dashboard is the React frontend in `securevision_frontend`
- `main.py` and `ui/` represent a legacy Streamlit path
- `core_pipeline/layer2_logic.py` is not the active fight path
- `src/components/VideoFeed.tsx` in the frontend is not part of the current runtime flow and still references an older MJPEG endpoint

## Startup

### Backend
```powershell
cd securevision_core
.\venv\Scripts\python.exe run_system.py
```

### Required Environment
Important environment variables include:

- `OPENAI_API_KEY`
- `OPENAI_MODEL=gpt-4o-mini`
- PostgreSQL connection settings loaded through `config.py` / `.env`
- Cloudinary credentials if evidence upload is enabled

## API

### WebSocket
- `ws://localhost:8001/ws/stats`

### REST
- `GET /api/stats`
- `GET /api/summary/daily`
- `GET /api/cameras`
- `PUT /api/cameras`
- `POST /auth/login`
- `POST /auth/signup`
- `DELETE /users/me`

## Models In Use
The active code path references:

- `models/yolo11n.pt`
- `models/weapon_detection4.pt`
- `models/pose26n.pt`
- `models/fightnet_best_model.pt`

Fallback behavior:

- `yolo11n-pose.pt` at the repo root is only a pose-model fallback
- it is not part of the normal primary model set
