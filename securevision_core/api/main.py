import asyncio
import os
import queue
import sys
import time
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api import auth, users
from agents.summary_agent import SummaryAgent
from auth import get_current_user, get_user_from_token
from database import SessionLocal, engine
from models_db import Base, User
from runtime_gate import activate_runtime, deactivate_runtime
from utils.camera_registry import CameraRegistry
from utils.logger import setup_logger
from utils.stats_manager import StatsManager


class CameraConfig(BaseModel):
    id: str
    name: str
    sector: str
    area: str
    is_active: bool = True


class CameraConfigPayload(BaseModel):
    cameras: List[CameraConfig]


Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)
app.include_router(users.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = setup_logger()
active_connections: List[WebSocket] = []
connection_last_seen: Dict[WebSocket, float] = {}
log_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
HEARTBEAT_TIMEOUT_SECONDS = 3.0


def broadcast_log_sync(log_entry: Dict[str, Any]):
    log_queue.put(log_entry)


def _authenticate_websocket(token: str | None) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing websocket token")

    db: Session = SessionLocal()
    try:
        return get_user_from_token(token, db)
    finally:
        db.close()


@app.websocket("/ws/stats")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    try:
        user = _authenticate_websocket(token)
    except HTTPException:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    active_connections.append(websocket)
    connection_last_seen[websocket] = time.time()
    activate_runtime()
    logger.info("[WS AUTH] Accepted stats websocket for user=%s", user.username)
    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                connection_last_seen[websocket] = time.time()
                if message == "logout":
                    break
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        connection_last_seen.pop(websocket, None)
        deactivate_runtime()


async def broadcaster():
    while True:
        while not log_queue.empty():
            data = log_queue.get()
            stale_connections: List[WebSocket] = []
            for connection in active_connections:
                try:
                    await connection.send_json(data)
                except Exception:
                    stale_connections.append(connection)
            for connection in stale_connections:
                if connection in active_connections:
                    active_connections.remove(connection)
                    connection_last_seen.pop(connection, None)
                    deactivate_runtime()
        await asyncio.sleep(0.05)


async def stale_connection_reaper():
    while True:
        now = time.time()
        stale_connections = [
            connection
            for connection, last_seen in list(connection_last_seen.items())
            if (now - last_seen) > HEARTBEAT_TIMEOUT_SECONDS
        ]
        for connection in stale_connections:
            try:
                await connection.close(code=1001)
            except Exception:
                pass
            if connection in active_connections:
                active_connections.remove(connection)
            connection_last_seen.pop(connection, None)
            deactivate_runtime()
        await asyncio.sleep(1.0)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcaster())
    asyncio.create_task(stale_connection_reaper())


@app.get("/api/stats")
def get_historical_stats(current_user: User = Depends(get_current_user)):
    manager = StatsManager()
    return manager.get_stats()


@app.get("/api/summary/daily")
def get_daily_summary(date: str = None, current_user: User = Depends(get_current_user)):
    manager = StatsManager()
    summary_agent = SummaryAgent(manager)
    return summary_agent.generate_daily_summary(date)


@app.get("/api/cameras")
def get_cameras(current_user: User = Depends(get_current_user)):
    registry = CameraRegistry()
    return {"cameras": registry.list_cameras(), "default_camera_id": "cam_01"}


@app.put("/api/cameras")
def update_cameras(payload: CameraConfigPayload, current_user: User = Depends(get_current_user)):
    registry = CameraRegistry()
    cameras = registry.save_cameras([camera.dict() for camera in payload.cameras])
    return {"cameras": cameras, "default_camera_id": "cam_01"}
