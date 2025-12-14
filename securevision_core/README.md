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

## Configuration

Settings can be adjusted in `config.py`:

-   **Video Source**: `VIDEO_PATH` (default: `testvideos/test-ismaeel2.mp4`)
-   **Timers**:
    -   `ABANDONED_DURATION_FRAMES`: Frames before luggage is considered abandoned (default: 150 frames / ~5s).
    -   `SUSTAINED_DURATION_FRAMES`: Frames to confirm a fight.
-   **Detection Classes**: `WEAPON_CLASSES`, `LUGGAGE_CLASSES`.

## System Architecture

### Frontend (`ui/`)
Built with **Streamlit**, providing a reactive web interface.
-   `main_dashboard.py`: The core application loop. Handles video display and log updates.
-   `Home.py`: Landing page.

### Backend Pipeline (`core_pipeline/`)
The `SecureVisionPipeline` class orchestrates the analysis:
1.  **Layer 1 (Object Detection)**: YOLOv8 model (`real_layer1.py`) detects people, weapons, and luggage.
2.  **Tracker**: Maintains identity of objects across frames (`tracker_state.py`).
3.  **Layer 2 (Logic)**:
    -   **Fight Detection**: Checks proximity and motion patterns.
    -   **Luggage Association**: Links luggage to the nearest person ("owner"). If the owner moves away (`LUGGAGE_PROXIMITY_THRESHOLD`), a timer starts.
4.  **Stats Manager**: Logs events to `stats.json` for analytics.

## Directory Structure

```
securevision_core/
├── core_pipeline/      # AI logic and pipeline orchestration
├── mock_models/        # Placeholder model weights (if valid paths not set)
├── testvideos/         # Input video files
├── ui/                 # Streamlit frontend files
├── utils/              # Helper functions (logging, stats)
├── config.py           # Central configuration
├── main.py             # Entry point shim
├── requirements.txt    # Python dependencies
└── securevision.log    # Runtime logs
```
