
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import asyncio
import time
import os
import json
import logging
from typing import List

# Add parent dir to path to import securevision_core modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import VIDEO_PATH, PROCESSING_WIDTH, DISPLAY_WIDTH
from core_pipeline.pipeline import SecureVisionPipeline
from utils.logger import setup_logger
from api import auth, users
from database import engine
from models_db import Base

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = setup_logger()

# Global state for logs/stats
active_connections: List[WebSocket] = []
pipeline = SecureVisionPipeline(stream_id="api_stream")

@app.websocket("/ws/stats")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Just keep connection alive, we broadcast from the loop
            await websocket.receive_text()
    except Exception:
        active_connections.remove(websocket)


# Helper for Sync threads to broadcast to Async Websockets
def broadcast_log_sync(log_entry):
    """
    Called from the main thread (OpenCV loop) to send data to the event loop.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_log(log_entry), loop)
    except Exception:
        # Loop might not be accessible easily from here if uvicorn runs in thread.
        # Actually uvicorn creates its own loop in the thread.
        # We need a proper way to bridge. 
        # Ideally, we put the queue in valid scope.
        # For simplicity in this script, we can skip complex thread-safe queueing 
        # and just rely on the race-condition (it often works for demos) 
        # OR better: use a thread-safe Queue that the websocket endpoint polls?
        pass

# ... (We will fix the Sync-Async bridge in a better way if needed, 
# for now let's just keep the endpoint generic and try to hook active_connections)
# Actually, since uvicorn runs in a separate thread, we can't schedule coroutines onto it easily 
# without the loop reference.
# Let's simple use a global list and loop.
# But `active_connections` is shared memory (Global Interpreter Lock protects list ops).
# `send_json` is async. We need to run it in the loop.

# UPDATED STRATEGY: 
# We will use a simple polling mechanism in the WebSocket endpoint? 
# No, that's inefficient.
# Effective way: 
# 1. API thread runs loop.
# 2. Main thread sets a variable / queue.
# 3. API thread loop checks queue?
# Let's keep it simple: We won't broadcast perfectly from main thread to this specific uvicorn loop instance 
# without more complex code. 
# User asked for "Logs ... when I visit the link".
# We can just rely on the API itself to generate logs?
# No, the Pipeline runs in Main thread.
# OK, let's use a shared Queue.

import queue
log_queue = queue.Queue()

def broadcast_log_sync(log_entry):
    log_queue.put(log_entry)

@app.websocket("/ws/stats")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Check queue non-blocking
            # We want to send data when it arrives.
            # But we are inside an async handler for *one* client.
            # We need a broadcaster task.
            
            # Temporary "Push" mechanism:
            # We can sleep small amount and check queue?
            # Or use asyncio.Queue? But we write from Sync thread.
            
            # Simple Hack for Demo:
            # Just wait for messages? No, we need to push.
            # Let's just consume the queue and send to ALL?
            # Creating a dedicated broadcaster task would be best.
            await asyncio.sleep(0.1)
            
            # Flush queue to this client? 
            # No, queue is global. If one client reads, others miss it.
            # We need a broadcast system.
            pass 
            # Real implementation of Sync->Async bridge is tricky in 1 file.
            # Let's stick to the previous plan but just not error out.
            
    except Exception:
        pass
    finally:
        active_connections.remove(websocket)

# Background Broadcaster Task
async def broadcaster():
    while True:
        while not log_queue.empty():
            data = log_queue.get()
            for connection in active_connections:
                try:
                    await connection.send_json(data)
                except:
                    pass
        await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcaster())


