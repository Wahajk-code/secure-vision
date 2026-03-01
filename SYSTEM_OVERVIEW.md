# SecureVision System Overview

## 1. System Architecture
The **SecureVision** system is a real-time video surveillance analysis platform designed to detect security threats such as weapons, fights, and abandoned luggage. It follows a decoupled **Client-Server Architecture**:

- **Backend (`securevision_core`)**: Python-based computer vision engine that processes video feeds, runs AI models (YOLOv11), and exposes a WebSocket API.
- **Frontend (`securevision_frontend`)**: React/TypeScript web application that connects to the backend to display live analytics, alerts, and video feeds.

### Data Flow
1. **Video Ingestion**: The backend reads a video file (or stream) frame-by-frame using OpenCV.
2. **AI Processing**: Each frame passes through a pipeline (YOLOv11 + Logic Layers).
3. **State Management**: Objects are tracked using BoTSORT, and their states (e.g., "Abandoning in 3s") are updated.
4. **Broadcasting**: Metadata and logs are sent via **WebSockets (`ws://localhost:8001/ws/stats`)** to the frontend.
5. **Visualization**: The frontend renders the data in real-time dashboards and charts.

---

## 2. Core Features (Deep Dive)

### A. Intelligent Weapon Detection
**Goal**: Instantly detect firearms and knives to trigger rapid response.
-   **How it works**:
    -   The system uses a custom-trained **YOLOv11** model to detect objects with classes `pistol` and `knife`.
    -   Unlike other objects, these trigger an **Immediate Critical Alert**. There is no "timer" or "sustained duration" check—detection implies immediate threat.
    -   **Code Path**: `core_pipeline/pipeline.py` checks `if cls in WEAPON_CLASSES: status="CRITICAL"`.

### B. Abandoned Luggage Detection
**Goal**: Identify bags left unattended in public spaces.
-   **How it works**:
    1.  **Ownership Assignment**: When a bag (`suitcase`, `backpack`) appears, the system calculates the Euclidean distance to all detected `person` objects. The closest person is assigned as the **Owner**.
    2.  **Distance Monitoring**: In every frame, we measure the distance between the Bag and its Owner.
    3.  **Timer Logic**: If the distance exceeds `LUGGAGE_PROXIMITY_THRESHOLD` (e.g., 2 meters), an internal timer starts (`abandoned_timer`).
    4.  **Alerting**:
        -   **Warning**: Timer > 0s (Yellow box, "Abandoning...").
        -   **Critical**: Timer > 5s (Red box, "ABANDONED LUGGAGE").
    5.  **Ghost Tracking**: If the owner walks behind a pillar (occlusion), **BoTSORT**'s Kalman Filter keeps their track alive ("Ghost") for a few seconds so the system doesn't falsely think the bag was abandoned just because the camera momentarily lost sight of the owner.

### C. Active Fight Detection
**Goal**: Detect violent physical interactions between individuals.
-   **How it works**:
    -   The system monitors the proximity of every Person-to-Person pair.
    -   **Sustained Proximity**: If two people are very close (< 1 meter) for a sustained period (e.g., > 2 seconds), it flags a "Potential Fight".
    -   **Future Expansion**: Currently relies on proximity and duration. A dedicated "Pose Estimation" or "Action Recognition" model (like LSTM or SlowFast) would be the next upgrade to distinguish between hugging and fighting.

### D. Real-Time Command Dashboard
**Goal**: Provide security operators with a single pane of glass for situational awareness.
-   **How it works**:
    -   **Live Command Table**: A dynamic list of every tracked object. It updates 30 times a second to show accurate status (Safe/Warning/Critical).
    -   **Interactive Alerts**: "Toasts" (popups) appear instantly for critical events, ensuring the operator sees them even if looking at a different screen.
    -   **Historical Analytics**: Uses **Recharts** to visualize trends (e.g., "Peak weapon detections were at 2:00 PM").

---

## 3. Design Decisions & Trade-offs (Why we chose X vs Y)

### Why YOLOv11 instead of Faster R-CNN or SSD?
-   **Reason**: **Speed & Efficiency**.
-   **Explanation**: Surveillance systems must run in **Real-Time** (30+ FPS). Older models like Faster R-CNN are accurate but too slow (5-10 FPS). YOLOv11 offers the best trade-off, providing state-of-the-art accuracy (SOTA) while remaining lightweight enough to run on standard GPUs alongside tracking logic.

### Why BoTSORT instead of Simple SORT or DeepSORT?
-   **Reason**: **Robustness to Occlusion**.
-   **Explanation**:
    -   **Simple SORT** relies only on motion (Kalman Filter); it fails if objects stop moving or cross paths.
    -   **DeepSORT** adds visual features but is older.
    -   **BoTSORT** combines the best of both: robust motion prediction (camera motion compensation) + good re-identification. This is crucial for the "Ghost Tracking" needed for the Abandoned Luggage logic.

### Why WebSockets instead of REST API (HTTP Polling)?
-   **Reason**: **Latency**.
-   **Explanation**: In a security context, a delay of 1-2 seconds is unacceptable.
    -   **HTTP Polling**: The frontend asks "Any new alerts?" every second. This introduces lag.
    -   **WebSockets**: The server *pushes* the alert to the frontend the *millisecond* it happens. This provides instant feedback for weapons or fights.

### Why React & TypeScript instead of basic HTML/JS?
-   **Reason**: **Maintainability & Complex State**.
-   **Explanation**: The dashboard handles complex, fast-changing state (30 updates/sec for 20+ objects).
    -   **React**: Efficiently updates only the changed parts of the DOM (Virtual DOM), preventing the page from freezing under load.
    -   **TypeScript**: Prevents bugs by ensuring we define strictly what an "Alert" looks like (`interface AlertMetadata`).

### Why PostgreSQL instead of a File/CSV?
-   **Reason**: **Structured Querying**.
-   **Explanation**: While a CSV is easy for logging, we need to answer complex questions like "Show me all weapon detections from last week between 2 PM and 4 PM." SQL databases perform these queries in milliseconds, whereas a file-based approach would require reading and parsing the entire history every time.
