# SecureVision Final Defense System

SecureVision is a comprehensive video analytics dashboard designed for public safety monitoring. It integrates multiple AI layers to detect weapons, fights, and abandoned luggage in real-time.

## Features

- **Live Monitoring**: Real-time video processing with visual annotations.
- **Weapon Detection**: Identifies guns and knives using YOLOv8.
- **Fight Detection**: Analyzing behavioral patterns to detect physical altercations.
- **Abandoned Luggage**: Tracks luggage owner proximity and detects abandonment after a set duration.
- **Dashboard**: Interactive Streamlit interface for monitoring and logs.

## Prerequisites

- **Python 3.8+**
- **Virtual Environment** (Recommended)

## Installation

1.  **Clone/Navigate** to the project directory:
    ```bash
    cd securevision_core
    ```

2.  **Create and Activate Virtual Environment** (if not already done):
    *   **Windows (PowerShell)**:
        ```powershell
        python -m venv venv
        .\venv\Scripts\Activate.ps1
        ```
    *   **Linux/Mac**:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To start the SecureVision Dashboard:

```bash
# Ensure your virtual environment is activated
python main.py
```

*   The application will launch in your default web browser at `http://localhost:8501`.
*   If it doesn't open automatically, look for the URL in the terminal output.

## System Architecture & Logic

The core of the system lies in the `SecureVisionPipeline` class, which orchestrates data flow between detection models, state trackers, and logic analyzers efficiently frame-by-frame.

### 1. Pipeline Flow (`core_pipeline/pipeline.py`)
For every video frame:
1.  **Ingest**: The frame is converted to RGB.
2.  **Layer 1 (Detection)**: The YOLOv8 model detects objects (Persons, Weapons, Luggage).
3.  **Tracker Update**: Detections are fed into the `TrackerState`, which maintains history (centroids, bounding boxes) for every unique Track ID.
4.  **Logic Processing**:
    *   **Layer 2 (Fights)**: Analyzes spatial relationships between people.
    *   **Luggage Association**: Links tracking data to detection abandonment.
5.  **Annotation & Logging**: The frame is drawn upon with bounding boxes, status text, and alerts. Events are logged to `securevision.log` and `stats.json`.

### 2. Detailed Component Logic

#### A. Object Detection & Tracking (`core_pipeline/real_layer1.py`)
-   **Model**: Uses `ultralytics` YOLOv8 (loading `models/weaponDetection.pt` or standard weights).
-   **Tracking**: We utilize YOLO's built-in tracker (`model.track(..., persist=True)`). This assigns a unique `track_id` to each detected object, allowing us to follow it across frames even if it moves.

#### B. Tracker State (`core_pipeline/tracker_state.py`)
-   Acts as the short-term memory of the system.
-   Stores a `deque` (double-ended queue) of the last `N` positions (centroids) for every object.
-   This history is crucial for calculating **sustained** interactions (e.g., two people staying close together for 2 seconds) rather than instantaneous glitches.

#### C. Abandoned Luggage Logic (`core_pipeline/tracker_state.py`)
This logic determines if a piece of luggage has been left behind.
1.  **Separation**: In every frame, we separate all tracks into `Persons` and `Luggage`.
2.  **Association**: For each luggage item, we calculate the Euclidean distance to *all* visible people.
3.  **Owner Assignment**:
    -   The closest person is tentatively identified as the "Owner".
    -   If the distance to the owner is **less** than `LUGGAGE_PROXIMITY_THRESHOLD` (approx 2 meters), the luggage is "Safe", and the `abandoned_timer` is reset to 0.
4.  **Abandonment**:
    -   If the distance **exceeds** the threshold (owner walked away), the `abandoned_timer` increments by 1.
    -   If the timer exceeds `ABANDONED_DURATION_FRAMES` (configured to 150 frames / ~5 seconds), the status flips to **ABANDONED**, triggering a red alert.

#### D. Fight Detection (`core_pipeline/layer2_logic.py`)
Detects aggressive behavior between two individuals.
1.  **Pairwise Analysis**: We iterate through every possible pair of detected persons.
2.  **Proximity Check**: Calculate the distance between their centroids.
3.  **Sustained Interaction**:
    -   We look back at the history of both tracks over `SUSTAINED_DURATION_FRAMES` (e.g., 60 frames).
    -   If they have remained within `PROXIMITY_THRESHOLD_METERS` for the entire duration, it indicates a significant interaction, not just passing by.
4.  **Kinematics (Variance)**:
    -   We calculate the variance of the distance between them over that period. High variance implies erratic movement (struggling/fighting) rather than standing still.
    -   If Proximity + Sustained Duration + Kinematic Variance conditions are met, a **FIGHT** event is triggered.

## Configuration

Settings can be adjusted in `config.py`:

-   **Video Source**: `VIDEO_PATH` (default: `testvideos/test-ismaeel2.mp4`)
-   **Timers**:
    -   `ABANDONED_DURATION_FRAMES`: Default 150 (5s).
    -   `SUSTAINED_DURATION_FRAMES`: Default 60 (2s).
-   **Thresholds**:
    -   `LUGGAGE_PROXIMITY_THRESHOLD`: Pixels (default 200).
    -   `PROXIMITY_THRESHOLD_METERS`: Model-relative units (default 1.0).

## Directory Structure

```
securevision_core/
├── core_pipeline/      # AI logic (Tracker, Logic, YOLO wrapper)
├── mock_models/        # Placeholder model weights
├── models/             # Active model weights (weaponDetection.pt)
├── testvideos/         # Input video files
├── ui/                 # Streamlit frontend (Dashboard, Home)
├── utils/              # Helper functions (Logger, Stats)
├── config.py           # Central configuration
├── main.py             # Entry point
└── requirements.txt    # Python dependencies
```
