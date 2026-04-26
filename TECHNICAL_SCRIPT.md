# SecureVision Technical Script

This script is a presentation-oriented walkthrough of the current backend architecture.

## Slide 1: The Runtime Orchestrator
**Visual focus**: `run_system.py`

**Script**:
"The current SecureVision runtime starts from `run_system.py`. This file launches FastAPI in the background, opens a mixed surveillance playlist, reads frames through a dedicated video reader thread, and sends each frame into the AI pipeline.

It also acts as the bridge between raw computer vision output and operator-facing behavior. After the pipeline returns object states, `run_system.py` normalizes them, evaluates them with deterministic rules, queues speech, submits qualifying alerts to the agentic layer, and broadcasts the results to the frontend."

---

## Slide 2: The Core Pipeline
**Visual focus**: `SecureVisionPipeline`

**Script**:
"At the heart of the AI runtime is `SecureVisionPipeline`. This class orchestrates detection, tracking, fight analysis, luggage logic, annotation, and event logging hooks.

It does not make the final operator decision on its own. Instead, it returns structured object states that the alert layer can interpret consistently."

---

## Slide 3: Detection And Tracking
**Visual focus**: `real_layer1.py` and `tracker_state.py`

**Script**:
"The first stage is object detection and tracking.

`real_layer1.py` runs two YOLO models every frame:
- a base model for people and luggage
- a weapon model for gun/rifle classes

The outputs are normalized into tracks with IDs, bounding boxes, centroids, and confidence scores. `TrackerState` then stores short-term history for each track, which is essential for abandonment logic and movement-based reasoning."

---

## Slide 4: Fight Detection
**Visual focus**: `fight_detector.py`, `pose_filter.py`, `fightnet_integration.py`

**Script**:
"Fight detection is a gated multi-stage process.

We do not run pose or sequence analysis on every person in every frame. First, `fight_detector.py` checks proximity and body velocity to isolate suspicious pairs. Only then do we crop those ROIs for pose estimation using `pose_filter.py`.

If that pair stays suspicious long enough, the rolling pose buffer is passed to `fightnet_integration.py`, which loads the FightNet model and confirms whether the sequence looks like a real altercation."

---

## Slide 5: Luggage Ownership And Abandonment
**Visual focus**: `tracker_state.py`

**Script**:
"Abandoned luggage detection depends on memory, not just a single frame.

The system assigns luggage to the nearest persistent person identity. If that owner moves too far away, the unattended timer starts. Warning is delayed for a configured period, and critical status is reached only after the full abandonment timeout.

This helps reduce noise from stray bags, temporary occlusion, and normal crowd motion."

---

## Slide 6: Re-Identification
**Visual focus**: `reid_manager.py`

**Script**:
"One of the more advanced parts of the architecture is ReID. `reid_manager.py` uses MobileNetV3-based embeddings to keep person identity more stable even when tracker IDs change.

This matters because luggage logic depends on consistent ownership. If the tracker forgets someone for a moment, ReID helps preserve the same logical person."

---

## Slide 7: Deterministic Alert Rules
**Visual focus**: `event_normalizer.py` and `alert_rules.py`

**Script**:
"The pipeline output is converted into normalized events and then evaluated by the rule engine.

This is one of the most important architectural decisions in the project. `alert_rules.py` is the source of truth for severity, risk score, event classification, and spoken alert text. That means the operational decision remains deterministic and explainable."

---

## Slide 8: Agentic Layer
**Visual focus**: `operations_agent_layer.py`

**Script**:
"On top of the deterministic rules, we added an agentic layer for operator-facing intelligence.

The operations agent layer runs three agents:
- triage
- incident timeline
- operator actions

These agents use strict-JSON OpenAI responses with fallbacks. They do not change severity, event type, or risk score. Their role is to explain the incident, summarize how it is evolving, and present context-aware instructions to the operator."

---

## Slide 9: Persistence And Evidence
**Visual focus**: `stats_manager.py` and `cloudinary_helper.py`

**Script**:
"The system keeps both historical logs and visual evidence.

`stats_manager.py` writes enriched events into PostgreSQL. The stored payload is already aligned with the rule engine, so analytics and summaries can reuse the same operational interpretation.

For critical incidents, `cloudinary_helper.py` uploads evidence screenshots and broadcasts the hosted image URL back to the dashboard, along with camera metadata like sector and area."

---

## Slide 10: Frontend Control Layer
**Visual focus**: `DashboardLayout.tsx` and dashboard components

**Script**:
"The React dashboard is the operator control layer. It renders:
- live tracked objects
- critical incidents
- agentic summaries
- operator action plans
- screenshot evidence
- historical analytics

The frontend stays relatively presentation-focused. Most of the real operational logic lives on the backend, which keeps the system behavior more consistent and easier to audit."

---

## Slide 11: Key Takeaway
**Summary Script**:
"SecureVision is structured around clear separation of concerns:

- perception in the computer vision pipeline
- deterministic decision-making in the alert rules
- operator assistance in the agentic layer
- persistence in the database and evidence services
- visualization in the React dashboard

That separation is what makes the system easier to evolve without losing operational control."
