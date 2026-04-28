# SecureVision System Presentation

## Slide 1: Introduction
**Title**: SecureVision - Real-Time AI Surveillance  
**Tagline**: "Deterministic Threat Detection With Agentic Operator Guidance"

**Talking Points**:
- SecureVision is built for live monitoring of weapons, fights, and abandoned luggage.
- The system combines computer vision, rule-based alerting, evidence capture, and an operator dashboard.
- The latest version also includes an agentic assistance layer for summaries, incident timelines, and action plans.

---

## Slide 2: High-Level Architecture
**Visual**: Camera/Video Source -> AI Runtime -> Alert Rules -> Agentic Layer -> Dashboard

**Key Components**:
1. **Backend Runtime**
   - Python + FastAPI
   - Processes video feeds frame-by-frame only while an authenticated dashboard session is active
   - Broadcasts real-time updates over authenticated WebSockets
2. **Frontend Dashboard**
   - React + TypeScript
   - Displays live targets, incidents, screenshots, and analytics
3. **Database**
   - PostgreSQL stores security event history

---

## Slide 3: AI Engine
**Core Logic**: `securevision_core`

- **Object Detection**
  - YOLO base model for people and luggage
  - dedicated weapon model for gun/rifle classes
- **Tracking**
  - BoTSORT object tracking
  - ReID for more persistent person identity
- **Fight Detection**
  - proximity
  - velocity
  - pose verification
  - FightNet sequence confirmation
- **Luggage Logic**
  - owner assignment
  - unattended warning delay
  - critical abandonment timeout

---

## Slide 4: Deterministic Operational Alerting
**Design Principle**: "Rules decide the threat level"

- `alert_rules.py` is the source of truth for:
  - event type
  - subtype
  - severity
  - risk level
  - risk score
  - spoken message
  - recommended action
- repeated alerts are suppressed with cooldown logic
- TTS is non-blocking and cooldown-aware

This is important because operator trust depends on stable, explainable decisions.

---

## Slide 5: Agentic Assistance Layer
**Design Principle**: "AI explains, but does not override"

The LangChain-backed bounded agentic layer provides:

1. **Alert Triage Agent**
   - dashboard title
   - operator summary
   - risk explanation
2. **Incident Timeline Agent**
   - incident title
   - timeline summary
   - recommended next step
3. **Operator Action Agent**
   - action plan
   - operator note
   - escalation hint

Important rule:

- LangChain does not control severity, event type, risk score, or whether an alert is real.

---

## Slide 6: User Interface
**Frontend Experience**:

- Live Command table for active tracked objects
- Active Incidents panel for critical incidents
- Agentic alert card for highlighted incident summaries
- Operator action card for response guidance
- Screenshot/evidence gallery
- Live FPS display
- Working session/timeline evidence filters
- Analytics and historical event views
- Camera/sector/area settings

---

## Slide 7: Data And Evidence
**Persistence Layer**:

- PostgreSQL stores historical security events
- event payloads are enriched before insert
- Cloudinary stores critical evidence images
- screenshot metadata includes camera, sector, area, and stream ID

---

## Slide 8: Current Detection Behavior
**Weapon**
- requires sustained confirmation frames
- person presence required for operational flagging

**Fight**
- suspicious pairs are gated before pose/FightNet
- warning and critical states are distinct

**Luggage**
- warning begins only after unattended delay
- critical happens after 10 seconds

---

## Slide 9: Technology Stack
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| Detection | Ultralytics YOLO | Object detection/tracking |
| Fight verification | Pose model + FightNet | Fight confirmation |
| Runtime | Python + OpenCV | Video processing |
| API | FastAPI + Uvicorn | REST + WebSockets |
| Dashboard | React + Vite + TypeScript | Operator UI |
| Analytics | Recharts | Historical visualization |
| Storage | PostgreSQL | Event history |
| Evidence | Cloudinary | Critical screenshot hosting |
| Agentic layer | LangChain + OpenAI API | Summaries and operator guidance |

---

## Slide 10: Demonstration Flow
1. Start backend runtime
2. Start React dashboard
3. Login to activate the protected dashboard session
4. Observe live target tracking
5. Trigger a warning or critical event
6. Show:
   - rule-based alert
   - spoken notification
   - screenshot/evidence upload
   - agentic incident/action summary for qualifying incidents

---

## Slide 11: Conclusion
- SecureVision is modular and operationally focused
- deterministic rules keep the alerting trustworthy
- the agentic layer improves clarity without taking control away from the rule engine
- the system is ready for further cleanup, scaling, and deployment hardening
