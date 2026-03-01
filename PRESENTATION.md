# SecureVision System Presentation

## Slide 1: Introduction
**Title**: SecureVision - AI-Powered Real-Time Surveillance
**Tagline**: "Advanced Threat Detection & Intelligent Tracking"

**Talking Points**:
-   Welcome to the customized SecureVision platform.
-   Designed to solve critical security challenges: Unattended Luggage, Weapon Detection, and Active Fighting.
-   Uses a hybrid Client-Server architecture for maximum performance.

---

## Slide 2: High-Level Architecture
**Visual**: [Diagram of Camera -> Backend (AI) -> Frontend (Dashboard)]

**Key Components**:
1.  **Backend (The Brain)**:
    -   Built with **Python** & **FastAPI**.
    -   Processes video feeds frame-by-frame.
    -   Hosted continuously to monitor streams.
2.  **Frontend (The Control Center)**:
    -   Built with **React** & **TypeScript**.
    -   Connected via real-time **WebSockets**.
    -   Provides instant alerts and live visualizations.

---

## Slide 3: The AI Engine (Backend)
**Core Logic**: `securevision_core`

-   **Object Detection**:
    -   Powered by **YOLOv11** (State-of-the-art accuracy).
    -   Detects: Person, Suitcase, Backpack, Handbag, Weapon (Pistol/Knife).
-   **Intelligent Tracking**:
    -   Uses **BoTSORT** to track objects moving across the screen.
    -   **Re-Identification (ReID)**: "Remembers" people even if they leave and re-enter the camera view, ensuring consistent tracking logic.
-   **Logic Layers**:
    -   Calculates distance between **Luggage** and **Owners**.
    -   Triggers alerts if luggage is alone for >10 seconds (Configurable).

---

## Slide 4: User Interface (Frontend)
**Design Philosophy**: "Future-Proof & High-Visibility"

-   **Dashboard**:
    -   Glassmorphism design (translucent dark UI).
    -   **Live Command Table**: Shows every active object and its status (Safe/Warning/Critical).
-   **Analytics**:
    -   Historical charts showing trends in weapon detections or abandoned items over time.
-   **Alerts**:
    -   Instant Toast notifications for critical threats.
    -   Visual indicators (Red/Yellow boxes) on the live feed.

---

## Slide 5: Key Libraries & Tech Stack
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **AI Model** | Ultralytics YOLOv11 | Object Detection |
| **CV Library** | OpenCV (Python) | Video Processing |
| **API** | FastAPI + Uvicorn | Server & WebSockets |
| **UI Framework** | React 18 + Vite | Frontend Application |
| **Styling** | Tailwind CSS | Rapid, Modern Styling |
| **Data Viz** | Recharts | Analytics Charts |

---

## Slide 6: Demonstration
**What we will see**:
1.  **System Startup**: Launching the backend engine.
2.  **Live Tracking**: Seeing the system identify people and bags in real-time.
3.  **Use Case - Abandoned Luggage**:
    -   Person leaves bag.
    -   Timer counts down.
    -   **ALERT** triggers on Dashboard.
4.  **Use Case - Weapon**:
    -   Immediate Critical Alert upon detection.

---

## Slide 7: Conclusion
-   SecureVision is a robust, modular solution.
-   Ready for deployment and scalable to multiple streams.
-   Combines powerful AI with a user-friendly modern interface.
