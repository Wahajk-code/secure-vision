# SecureVision: AI Agent Context & System Architecture

This document is designed to provide immediate context for any AI coding agent (Cursor, GitHub Copilot, Google DeepMind Agent, etc.) interacting with the **"SecureVision"** repository. It outlines the core deep learning architecture, the sequential filtering pipeline, and the directory structure so you can navigate the codebase seamlessly.

## 1. High-Level Architecture
SecureVision is a real-time smart surveillance pipeline. It fundamentally solves the issue of heavy, computationally expensive AI (Pose Estimation, Temporal Analysis) by utilizing a **Multi-Gated Filtering System**. 

Instead of running expensive ML models on every frame, SecureVision uses O(N) or O(N²) heuristic filters on metadata (bounding box centroids, basic velocities) to isolate "suspicious candidates" before passing those specific crops to heavy GPU models.

### Key Capabilities
1. **Weapon Detection**: Direct object detection of guns and knives at low-confidence thresholds.
2. **Abandoned Luggage Detection**: Spatial tracking of owners + luggage association over long time windows (150-frame ghosting tolerance).
3. **Fight Detection**: A highly complex hybrid pipeline combining Proximity → Body Velocity → Limbs/Contact Geometry (Pose) → 30-Frame Sequence Model (FightNet).
4. **Re-Identification (ReID)**: MobileNetV3 feature extraction to reliably map disjoint tracking IDs across occlusion boundaries to persistent Person IDs.

---

## 2. Directory Structure & File Map

### Core Pipeline (`securevision_core/core_pipeline/`)
This is the heart of the system.
* **`pipeline.py`**: The `SecureVisionPipeline` master orchestrator. Takes raw RGB frames from OpenCV, passes them to Layer 1, updates the tracker, and evaluates fight/luggage states. Returns a data packet that `run_system.py` broadcasts to the React frontend.
* **`real_layer1.py`**: Runs YOLOv8/11 instance loaded from `weapon_detection3.pt`. Extracts raw bounding boxes for People, Guns, Knives, and Luggage. Filters them against `CONFIDENCE_THRESHOLDS` located in `config.py`.
* **`tracker_state.py`**: Manages the persistence of bounding boxes across frames using `BoTSORT`. It tracks memory of where objects were, calculating Euclidean distance between bags and people for ownership claims.
* **`reid_manager.py`**: Uses a MobileNetV3 + Cosine Similarity framework. Extracts feature embeddings from tracked people crops every ~30 frames to guarantee tracking fidelity even if BoTSORT drops an ID.
* **`fight_detector.py`**: The First Gate for fight detection. Checks Proximity (<150px) between two people. If sustained, it measures Body Velocity. If violently moving, it triggers the Pose Filter. Maintains a 30-frame keypoint rolling buffer (`active_pairs`).
* **`pose_filter.py`**: The Second Gate. Runs `yolov8m-pose.pt` exclusively on pairs flagged by `fight_detector`. Calculates "Arm Velocity" and "Wrist-to-Torso Contact Distance".
* **`fightnet_integration.py`**: The Final Model. Converts the 30-frame skeleton history from `pose_filter` into a 150-Dimensional sequence matrix. Passes it through the proprietary 1D-CNN + SE-Block + Attention PyTorch model (`fightnet_best_model.pt`) to output a >0.40 confidence probability.

### Entry & Config (`securevision_core/`)
* **`run_system.py`**: The main execution loop. Spawns the FastAPI threading, handles the video `cv2.VideoCapture()` playlist loops, resizes frames dynamically to `PROCESSING_WIDTH`, and emits WebSocket payloads.
* **`api/main.py`**: A FastAPI backend that hosts the WebSocket connections necessary to feed telemetry to the frontend.
* **`config.py`**: The master configuration switchboard. Modifying `CONFIDENCE_THRESHOLDS` or video playlists here propagates throughout the entire system.

### Frontend (`securevision_frontend/`)
React/Vite dashboard that visualizes the JSON logs emitted by the backend. 
* Uses **WebSockets** to display critical threats and tracking events in real-time.

---

## 3. Important Design Principles for AI Agents

When writing or modifying code in this repository, rigidly adhere to these principles:

1. **The Gating Principle**: Do NOT execute ML inference on the whole frame if it can be avoided. Operations like Pose Estimation or ReID Feature Extraction must ONLY be run on tight `cv2` ROIs (Regions of Interest) explicitly yielded by BoTSORT/Layer 1, and only if a heuristic (velocity, proximity) justifies it.
2. **GPU Optimization via `cuda`**: Ensure all models (`FightNet`, `MobileNetV3`, `YOLO`) explicitly map their tensors back and forth to `.to('cuda')` and `.cpu().numpy()` at the right boundaries.
3. **Ghost Tracking Tolerance**: The system operates with "Ghost Frames" for luggage and fights. If an object is momentarily lost by YOLO (e.g., occlusion), the tracker and logic layers assume the object maintains its state for ~150 frames. Do not automatically dump state if a bounding box vanishes for 2 frames.
4. **Separation of Concerns**: 
   - `real_layer1.py` handles pure detection.
   - `tracker_state.py` handles persistent geography.
   - `fight_detector.py` handles sliding-window business logic.
   - `pipeline.py` acts strictly as the router/decorator.
5. **Config First**: Always parameterize thresholds into `config.py` rather than hardcoding them into the pipeline (e.g., `CONFIDENCE_THRESHOLDS`, `MIN_CONFIDENCE`, `FIGHT_PROXIMITY_THRESHOLD_PIXELS`).

## 4. How the Flow of Data Works

1. `test1.mp4` -> `run_system.py`
2. Resized Frame -> `SecureVisionPipeline.process_frame()`
3. Frame -> `real_layer1.py` -> Raw Bounding Boxes -> `TrackerState`
4. `TrackerState` -> Mapped Tracks -> `fight_detector.process()`
5. `fight_detector` -> finds fast moving pair -> `pose_filter.py` -> 30-Frame Sequence Buffer
6. **(Sequence Reaches 15+ Frames)** -> `fightnet_integration.py` -> `True/False`
7. Dashboard Data Packet compiled + Annotated Frame drawn -> returned to `run_system.py`.
8. `run_system.py` -> `broadcast_log_sync` -> `api/main.py` -> React Frontend UI.
