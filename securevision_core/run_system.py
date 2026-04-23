
import cv2
import threading
import uvicorn
import time
import asyncio
import os
import signal
import sys
import sys
import queue
from typing import Dict, List

from api.main import app, broadcast_log_sync
from config import VIDEO_PATH, PROCESSING_WIDTH
from agents.alert_rules import AlertRuleEngine
from agents.event_normalizer import normalize_pipeline_item
from agents.tts_agent import TTSAgent
from core_pipeline.pipeline import SecureVisionPipeline
from utils.logger import setup_logger
from utils.cloudinary_helper import upload_image_async
from utils.camera_registry import CameraRegistry

# Setup Logger
logger = setup_logger()

# Global Flag for Graceful Shutdown
running = True

class VideoReaderThread(threading.Thread):
    """
    Dedicated thread for continuously reading video frames from disk/stream into an in-memory queue.
    This hides the I/O and MP4 decoding latency from the heavy AI processing loop.
    """
    def __init__(self, playlist: List[Dict], queue_size=60):
        super().__init__(daemon=True)
        self.playlist = playlist
        self.frame_queue = queue.Queue(maxsize=queue_size)
        self.current_idx = 0
        self.cap = cv2.VideoCapture(self.current_entry["source"])
        self._is_running = True

    @property
    def current_entry(self):
        return self.playlist[self.current_idx]

    def run(self):
        entry = self.current_entry
        logger.info(
            "[VideoReader] Starting mixed feed. Source=%s camera=%s",
            os.path.basename(entry["source"]),
            entry["camera_id"],
        )
        while self._is_running:
            if not self.cap.isOpened():
                break
            
            ret, frame = self.cap.read()
            if not ret:
                # Video Ended. Advance playlist.
                self.current_idx = (self.current_idx + 1) % len(self.playlist)
                entry = self.current_entry
                next_video = os.path.basename(entry["source"])
                logger.info(
                    "[VideoReader] Switching mixed feed to %s (%s)",
                    entry["camera_id"],
                    next_video,
                )
                self.cap.release()
                
                # Signal the AI thread perfectly in sync with the frame offset that the context has changed
                self.frame_queue.put(("VIDEO_RESET", None, entry))
                self.cap = cv2.VideoCapture(entry["source"])
                continue
                
            # Block if Queue is full, preventing RAM overflow while still staying 60 frames ahead of the AI
            self.frame_queue.put(("FRAME", frame, self.current_entry))

    def stop(self):
        self._is_running = False
        if self.cap.isOpened():
             self.cap.release()


# Alert state windows
# Repeat active incidents every 5 seconds, but forget a disappeared
# incident quickly so a new instance is not swallowed by stale cooldown.
alert_states = {}
ALERT_REPEAT_SECONDS = 5.0
ALERT_PERSISTENCE_SECONDS = 2.0

alert_rules = AlertRuleEngine()
camera_registry = CameraRegistry()
tts_agent = TTSAgent(cooldown_seconds=5.0, enabled=os.getenv("SECUREVISION_TTS_ENABLED", "1") != "0")
alert_group_sent = {}


def build_alert_key(camera_id, decision, raw_event):
    track_id = raw_event.get("track_id")
    if track_id is None:
        track_id = "unknown"
    return f"{camera_id}:{decision.event_type}:{decision.subtype}:{track_id}:{decision.severity}"


def build_alert_group_key(camera_id, decision, raw_event):
    """
    Suppress related weapon detections in the same camera/place for 5 seconds.
    Fight and luggage alerts remain instance-specific.
    """
    if decision.event_type == "WEAPON":
        location = "|".join([
            str(raw_event.get("camera_id") or camera_id),
            str(raw_event.get("sector") or ""),
            str(raw_event.get("area") or ""),
        ])
        return f"{location}:{decision.event_type}:{decision.subtype}:{decision.severity}"
    return build_alert_key(camera_id, decision, raw_event)


def handle_operational_alert(item, stream_id="desktop_stream", camera_id="cam_01"):
    """
    Converts raw pipeline objects into deterministic operational alerts,
    broadcasts them to the dashboard, and queues speech when rules allow it.
    """
    camera = camera_registry.get_camera(camera_id)
    raw_event = normalize_pipeline_item(item, stream_id=stream_id, camera=camera)
    if raw_event["event_type"] == "UNKNOWN":
        return

    decision = alert_rules.evaluate(raw_event)
    if not decision.should_alert:
        return

    alert_key = build_alert_key(camera_id, decision, raw_event)
    group_key = build_alert_group_key(camera_id, decision, raw_event)
    current_time = time.time()
    state = alert_states.setdefault(alert_key, {"first_seen": current_time, "last_seen": current_time, "last_sent": 0})
    state["last_seen"] = current_time

    last_sent = alert_group_sent.get(group_key, 0)
    if current_time - last_sent <= ALERT_REPEAT_SECONDS:
        logger.debug(
            "[ALERT SUPPRESSED] key=%s group=%s next_repeat_in=%.1fs",
            alert_key,
            group_key,
            ALERT_REPEAT_SECONDS - (current_time - last_sent)
        )
        return alert_key

    logger.info(
        "[ALERT TRIGGERED] key=%s group=%s severity=%s score=%s location=%s/%s/%s message=%s",
        alert_key,
        group_key,
        decision.severity,
        decision.score,
        raw_event.get("camera_name", camera_id),
        raw_event.get("sector", "Unknown Sector"),
        raw_event.get("area", "Unknown Area"),
        decision.dashboard_message,
    )

    broadcast_log_sync(decision.to_websocket_payload())
    speech_queued = tts_agent.enqueue_decision(decision)
    if speech_queued:
        logger.info("[TTS QUEUED] key=%s speech=%s", alert_key, decision.spoken_message)
    elif decision.should_speak:
        logger.info("[TTS SUPPRESSED] key=%s reason=cooldown_or_disabled", alert_key)
    state["last_sent"] = current_time
    alert_group_sent[group_key] = current_time
    return alert_key


def cleanup_alert_states(seen_keys):
    now = time.time()
    for key, state in list(alert_states.items()):
        if key in seen_keys:
            continue
        if now - state.get("last_seen", 0) > ALERT_PERSISTENCE_SECONDS:
            logger.info("[ALERT CLEARED] key=%s inactive_for=%.1fs", key, now - state.get("last_seen", 0))
            del alert_states[key]


def run_api():
    """Runs the FastAPI server."""
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

def signal_handler(sig, frame):
    global running
    print("\n[INFO] Exiting SecureVision System...")
    running = False

def main():
    global running
    
    # Register Signal Handler
    signal.signal(signal.SIGINT, signal_handler)

    # 1. Start API in Background Thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info("FastAPI Server started on http://localhost:8001")

    # 3. Start Video Pipeline (Main Thread)
    video_dir = os.path.join(os.path.dirname(__file__), 'testvideos')
    playlist = [
        {"source": os.path.join(video_dir, 'gunmantest3.mp4'), "camera_id": "cam_01"},
        {"source": os.path.join(video_dir, 'test6.mp4'), "camera_id": "cam_02"},
        {"source": os.path.join(video_dir, 'fight1final.mp4'), "camera_id": "cam_03"},
        {"source": os.path.join(video_dir, 'fight2final.mp4'), "camera_id": "cam_04"},
        {"source": os.path.join(video_dir, 'luggage1final.mp4'), "camera_id": "cam_01"},
        {"source": os.path.join(video_dir, 'luggage2final.mp4'), "camera_id": "cam_02"},
    ]
    
    # 3. Start Async Video Reader Thread
    video_reader = VideoReaderThread(playlist, queue_size=60)
    video_reader.start()

    initial_camera = camera_registry.get_camera("cam_01")
    pipeline = SecureVisionPipeline(stream_id="desktop_stream_cam_01")
    frame_count = 0
    
    logger.info("Opening Native Video Window for playlist. Waiting for AI loop to spin up...")
    logger.info(
        "[MIXED FEED] Now showing %s / %s / %s",
        initial_camera.get("name"),
        initial_camera.get("sector"),
        initial_camera.get("area"),
    )
    logger.info("Press 'Q' in the video window to quit.")

    while running:
        # Pull pre-decoded frame instantly from memory (will block lightly if thread is catching up)
        try:
            action, frame, source_entry = video_reader.frame_queue.get(timeout=1.0)
        except queue.Empty:
            continue # Try again
            
        if action == "VIDEO_RESET":
            # Reset entire pipeline state perfectly in-sync with the frame flip to prevent ID ghosting
            alert_states.clear()
            alert_group_sent.clear()
            camera = camera_registry.get_camera(source_entry["camera_id"])
            pipeline = SecureVisionPipeline(stream_id=f"desktop_stream_{source_entry['camera_id']}")
            frame_count = 0
            logger.info(
                "[MIXED FEED] Now showing %s / %s / %s",
                camera.get("name"),
                camera.get("sector"),
                camera.get("area"),
            )
            continue

        camera_id = source_entry["camera_id"]
        camera = camera_registry.get_camera(camera_id)
            
        frame_count += 1
        start_time = time.time()
        
        # Validation / Processing
        # Convert to RGB for Pipeline
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Optimization: Resize for Process
        h, w = frame_rgb.shape[:2]
        aspect_ratio = h / w
        process_h = int(PROCESSING_WIDTH * aspect_ratio)
        frame_small = cv2.resize(frame_rgb, (PROCESSING_WIDTH, process_h))
        
        # Cloudinary Callback
        def on_critical_capture(frame_to_upload, description):
            # Send current time for metadata
            timestamp = time.strftime("%H:%M:%S")
            upload_image_async(frame_to_upload, description, timestamp)
            
        # Run Heavy Pipeline
        annotated_frame, status, log_data = pipeline.process_frame(frame_small, frame_count, capture_callback=on_critical_capture)
        
        # Broadcast Logs to API/Frontend
        if log_data:
            seen_alert_keys = set()
            for item in log_data:
                if item.get("status") in {"WARNING", "CRITICAL"}:
                    key = handle_operational_alert(
                        item,
                        stream_id=f"desktop_stream_{camera_id}",
                        camera_id=camera_id,
                    )
                    if key:
                        seen_alert_keys.add(key)
            cleanup_alert_states(seen_alert_keys)
        else:
            cleanup_alert_states(set())

        if frame_count % 3 == 0: # Broadcast objects every 3rd frame to save bandwidth
             broadcast_log_sync({
                 "type": "LIVE_FEED",
                 "objects": log_data, # log_data is now 'luggage_dashboard_data' which contains all objects
                 "camera": camera,
                 "timestamp": time.strftime("%H:%M:%S")
             })
             
        # Calculate Dynamic FPS
        elapsed = time.time() - start_time
        current_fps = 1.0 / elapsed if elapsed > 0 else 30.0

        if frame_count % 300 == 0:
             broadcast_log_sync({
                 "fps": round(current_fps, 1),
                 "log": {
                     "type": "INFO", 
                     "message": f"Pipeline Running - Frame {frame_count}",
                     "timestamp": time.strftime("%H:%M:%S")
                 }
             })

        # Display Native Window
        # Convert back to BGR for OpenCV imshow
        frame_bgr_out = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
        cv2.putText(
            frame_bgr_out,
            f"{camera.get('name')} | {camera.get('sector')} | {camera.get('area')}",
            (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        cv2.imshow("SecureVision", frame_bgr_out)
        
        # Yield GIL to allow API thread to run
        time.sleep(0.005)

        # Exit on 'Q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    running = False
    video_reader.stop()
    video_reader.join(timeout=2.0)
    cv2.destroyAllWindows()
    logger.info("System Shutdown Complete.")
    sys.exit(0)

if __name__ == "__main__":
    main()
