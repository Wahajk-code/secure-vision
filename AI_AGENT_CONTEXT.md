# SecureVision AI Agent Context

This document gives a coding agent fast orientation for the current SecureVision codebase.

## 1. What The System Is
SecureVision is a real-time surveillance runtime that processes local video streams, detects threats, applies deterministic alert rules, and broadcasts operational data to a React dashboard.

Primary incident types:

- weapons
- fights
- abandoned luggage

Current runtime path:

- `securevision_core/run_system.py`
- `securevision_core/api/main.py`
- `securevision_core/core_pipeline/pipeline.py`

## 2. Core Design Principles

### 2.1 Deterministic Alerting First
The rule engine in `securevision_core/agents/alert_rules.py` is the source of truth for:

- severity
- event type
- risk score
- whether an alert should be raised
- spoken alert text

Do not move these decisions into the OpenAI layer.

### 2.2 Expensive Models Are Gated
The system avoids running heavy models on the whole frame where possible.

- YOLO runs on the frame for object detection/tracking
- pose inference runs only on suspicious person ROIs
- FightNet runs only after suspicious pair buffering
- ReID is used to stabilize identities across tracker churn

### 2.3 Alerting And Broadcasting Are Separate From Detection
The rough flow is:

1. `real_layer1.py` detects objects
2. `tracker_state.py` maintains history and luggage ownership
3. `fight_detector.py` evaluates suspicious person pairs
4. `pipeline.py` composes display/object state rows
5. `event_normalizer.py` turns rows into normalized events
6. `alert_rules.py` evaluates severity/score/action
7. `run_system.py` broadcasts alerts, queues TTS, submits agentic enrichment

### 2.4 OpenAI Is Explanation-Only
The OpenAI-backed layer in `securevision_core/agents/` is used only for:

- triage summaries
- incident timeline wording
- operator action plans

It must not override:

- `severity`
- `event_type`
- `risk_score`
- whether the detection is real
- whether the system should alert

### 2.5 Cost Control Matters
The agentic/OpenAI layer is not called per frame.

It is gated by:

- severity
- incident-update status
- cooldown windows

## 3. File Map

### 3.1 Active Backend Files
- `securevision_core/run_system.py`
  - main runtime loop
  - playlist handling
  - FastAPI thread startup
  - alert broadcasting
  - TTS queueing
  - agentic submission
- `securevision_core/api/main.py`
  - WebSocket broadcaster
  - stats/summary/camera/auth routes
- `securevision_core/config.py`
  - thresholds and model names

### 3.2 Core Pipeline
- `securevision_core/core_pipeline/pipeline.py`
  - main frame orchestrator
- `securevision_core/core_pipeline/real_layer1.py`
  - YOLO object detection/tracking
- `securevision_core/core_pipeline/tracker_state.py`
  - bbox/centroid history
  - luggage ownership
- `securevision_core/core_pipeline/fight_detector.py`
  - active fight detection path
- `securevision_core/core_pipeline/pose_filter.py`
  - pose ROI verification
- `securevision_core/core_pipeline/fightnet_integration.py`
  - sequence confirmation model
- `securevision_core/core_pipeline/reid_manager.py`
  - identity persistence

Important note:

- `securevision_core/core_pipeline/layer2_logic.py` exists, but it is not the active integrated fight path

### 3.3 Agent Layer
- `securevision_core/agents/event_normalizer.py`
- `securevision_core/agents/alert_rules.py`
- `securevision_core/agents/tts_agent.py`
- `securevision_core/agents/summary_agent.py`
- `securevision_core/agents/slm_service.py`
- `securevision_core/agents/alert_triage_agent.py`
- `securevision_core/agents/incident_timeline_agent.py`
- `securevision_core/agents/operator_action_agent.py`
- `securevision_core/agents/operations_agent_layer.py`

### 3.4 Utilities
- `securevision_core/utils/stats_manager.py`
- `securevision_core/utils/camera_registry.py`
- `securevision_core/utils/cloudinary_helper.py`
- `securevision_core/utils/logger.py`

### 3.5 Frontend
- `securevision_frontend/src/layouts/DashboardLayout.tsx`
- `securevision_frontend/src/components/LiveEventsTable.tsx`
- `securevision_frontend/src/components/StatsPanel.tsx`
- `securevision_frontend/src/components/AgenticAlertCard.tsx`
- `securevision_frontend/src/components/ActiveIncidentsPanel.tsx`
- `securevision_frontend/src/components/OperatorActionCard.tsx`
- `securevision_frontend/src/components/IncidentDetailModal.tsx`

## 4. Models In Use
The current active code path references:

- `securevision_core/models/yolo11n.pt`
- `securevision_core/models/weapon_detection4.pt`
- `securevision_core/models/pose26n.pt`
- `securevision_core/models/fightnet_best_model.pt`

There are additional older model artifacts in the repo, but the active runtime uses the list above.

Important clarification:

- `yolo11n-pose.pt` at the repo root is not the normal pose model
- it is only a fallback if `pose26n.pt` fails to load to CUDA in `pose_filter.py`

## 5. Important Runtime Rules

### 5.1 Weapon Flow
- base YOLO + weapon YOLO both run
- weapon boxes are filtered by confidence and size constraints
- person presence is required for operational weapon flagging
- confirmed weapons require `WEAPON_CONFIRMATION_FRAMES`

### 5.2 Fight Flow
- only close person pairs are evaluated
- velocity gates pose verification
- pose activity gates FightNet sequence confirmation
- warning and critical fight states are distinct

### 5.3 Luggage Flow
- luggage is assigned to nearest persistent person
- warning is delayed until `LUGGAGE_WARNING_DELAY_FRAMES`
- critical occurs at `ABANDONED_DURATION_FRAMES`

### 5.4 Speech And Cooldowns
TTS is non-blocking and cooldown-aware.

Important behavior:

- warnings for fights and luggage can be spoken
- repeated speech is deduped by event context, not just tracker ID
- critical fights have a stronger same-camera cooldown

## 6. Agentic Layer Behavior

### 6.1 `SLMService`
- uses `OPENAI_API_KEY`
- required model is `gpt-4o-mini`
- expects strict JSON
- has deterministic fallback responses
- disables model usage for the run if the API fails

### 6.2 `OperationsAgentLayer`
Pipeline:

1. triage
2. timeline
3. actions

It returns a payload like:

```json
{
  "type": "AGENTIC_ALERT",
  "triage": {},
  "incident": {},
  "actions": {},
  "original_event": {}
}
```

### 6.3 `OperatorActionAgent`
Starts with deterministic action templates and uses OpenAI only to personalize:

- `action_plan`
- `operator_note`
- `escalation_hint`

The personalization now uses:

- event subtype
- severity/risk level/risk score
- confidence
- camera/sector/area
- deterministic recommended action
- dashboard message
- triage summary
- incident timeline summary

## 7. Known Legacy / Cleanup Areas
- `securevision_core/main.py` and `securevision_core/ui/` are a legacy Streamlit path
- `securevision_frontend/src/components/VideoFeed.tsx` is not part of the current dashboard flow
- `securevision_core/core_pipeline/layer2_logic.py` is legacy
- `securevision_core/mock_models/` is not part of the current runtime
- `securevision_core/api/main.py` still contains some duplicated/comment-heavy scaffolding that could be cleaned up

## 8. Recommended Startup Path

1. Start PostgreSQL
2. Ensure the active model files are present
3. Set:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL=gpt-4o-mini`
4. Run `securevision_core/run_system.py`
5. Run the React frontend
6. Connect to `ws://localhost:8001/ws/stats`
