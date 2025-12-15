# SecureVision Final Defense System

SecureVision is a comprehensive video analytics dashboard designed for public safety monitoring. It integrates multiple AI layers to detect weapons, fights, and abandoned luggage in real-time.

**New Architecture**:
- **Backend**: FastAPI (Python) for video streaming and AI logic.
- **Frontend**: React (Vite + TypeScript) for a premium, responsive UI.

## Features

- **Live Monitoring**: Real-time video processing with visual annotations.
- **Weapon Detection**: Identifies guns and knives using YOLOv8.
- **Fight Detection**: Analyzing behavioral patterns to detect physical altercations.
- **Abandoned Luggage**: Tracks luggage owner proximity and detects abandonment after a set duration.
- **Real-time Analytics**: WebSocket-based event logging and FPS monitoring.

## Prerequisites

- **Python 3.8+**
- **Node.js & npm**
- **Virtual Environment** (Recommended)

## Installation & Usage

You need to run the **Backend** and **Frontend** in separate terminals.

### 1. Backend (FastAPI)

```bash
cd securevision_core
# Activate Virtual Environment (if not active)
.\venv\Scripts\Activate.ps1
# Install Dependencies (First time only)
pip install -r requirements.txt
# Run Server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
The API will run at `http://localhost:8000`.

### 2. Frontend (React)

```bash
cd securevision_frontend
# Install Dependencies (First time only)
npm install
# Run Dev Server
npm run dev
```
The Dashboard will launch at `http://localhost:5173`.

## Configuration

Settings can be adjusted in `securevision_core/config.py`:
- `VIDEO_PATH`: Path to input video.
- `PROCESSING_WIDTH`: Resolution for AI inference (Default: 640).
- `DISPLAY_WIDTH`: Resolution for display (Frontend assumes 100% width).

## System Architecture

### Backend (`securevision_core/`)
-   **`api/main.py`**: Entry point. Serves MJPEG stream (`/video_feed`) and WebSockets (`/ws/stats`).
-   **`core_pipeline/`**: Contains YOLO model (`model.track`), Tracker Logic, and Event detection.

### Frontend (`securevision_frontend/`)
-   Built with **React**, **TypeScript**, and **Tailwind CSS**.
-   **`VideoFeed.tsx`**: Consumes the MJPEG stream.
-   **`StatsPanel.tsx`**: Connects to WebSocket for real-time logs.
