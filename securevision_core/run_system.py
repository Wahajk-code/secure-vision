
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

from api.main import app, broadcast_log_sync
from config import VIDEO_PATH, PROCESSING_WIDTH, LUGGAGE_CLASSES
from core_pipeline.pipeline import SecureVisionPipeline
from utils.logger import setup_logger

# Setup Logger
logger = setup_logger()

# Global Flag for Graceful Shutdown
running = True

class VideoReaderThread(threading.Thread):
    """
    Dedicated thread for continuously reading video frames from disk/stream into an in-memory queue.
    This hides the I/O and MP4 decoding latency from the heavy AI processing loop.
    """
    def __init__(self, playlist, queue_size=60):
        super().__init__(daemon=True)
        self.playlist = playlist
        self.frame_queue = queue.Queue(maxsize=queue_size)
        self.current_idx = 0
        self.cap = cv2.VideoCapture(self.playlist[self.current_idx])
        self._is_running = True

    def run(self):
        logger.info(f"[VideoReader] Starting background decoding. Source: {os.path.basename(self.playlist[self.current_idx])}")
        while self._is_running:
            if not self.cap.isOpened():
                break
            
            ret, frame = self.cap.read()
            if not ret:
                # Video Ended. Advance playlist.
                self.current_idx = (self.current_idx + 1) % len(self.playlist)
                next_video = os.path.basename(self.playlist[self.current_idx])
                logger.info(f"[VideoReader] Video ended. Moving to next video in playlist: {next_video}")
                self.cap.release()
                
                # Signal the AI thread perfectly in sync with the frame offset that the context has changed
                self.frame_queue.put(("VIDEO_RESET", None))
                self.cap = cv2.VideoCapture(self.playlist[self.current_idx])
                continue
                
            # Block if Queue is full, preventing RAM overflow while still staying 60 frames ahead of the AI
            self.frame_queue.put(("FRAME", frame))

    def stop(self):
        self._is_running = False
        if self.cap.isOpened():
             self.cap.release()


# Alert Throttling State
# Dict[str, float] -> "LuggageID": timestamp
sent_alerts = {}
ALERT_COOLDOWN = 10.0 # Seconds before re-alerting for same luggage ID if it recurs


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
    logger.info("FastAPI Server started on http://localhost:8000")

    # 2. Add delay to let API start
    time.sleep(2)

    # 3. Start Video Pipeline (Main Thread)
    playlist = [
        os.path.join(os.path.dirname(__file__), 'testvideos', 'test6.mp4'),
        os.path.join(os.path.dirname(__file__), 'testvideos', 'test-ismaeel2.mp4'),
        os.path.join(os.path.dirname(__file__), 'testvideos', 'livefight-test3.mp4')
    ]
    
    # 3. Start Async Video Reader Thread
    video_reader = VideoReaderThread(playlist, queue_size=60)
    video_reader.start()

    pipeline = SecureVisionPipeline(stream_id="desktop_stream")
    frame_count = 0
    
    logger.info("Opening Native Video Window for playlist. Waiting for AI loop to spin up...")
    logger.info("Press 'Q' in the video window to quit.")

    while running:
        # Pull pre-decoded frame instantly from memory (will block lightly if thread is catching up)
        try:
            action, frame = video_reader.frame_queue.get(timeout=1.0)
        except queue.Empty:
            continue # Try again
            
        if action == "VIDEO_RESET":
            # Reset entire pipeline state perfectly in-sync with the frame flip to prevent ID ghosting
            pipeline = SecureVisionPipeline(stream_id="desktop_stream")
            frame_count = 0
            continue
            
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
        
        # Run Heavy Pipeline
        annotated_frame, status, log_data = pipeline.process_frame(frame_small, frame_count)
        
        # Broadcast Logs to API/Frontend
        if log_data:
            for item in log_data:
                # Check for Abandoned Luggage Alert
                # item structure: {id, category, status, details}
                if item.get("category") in LUGGAGE_CLASSES:
                    if "ABANDONED" in item.get("details", "") and item.get("status") == "CRITICAL":
                         lug_id = item['id']
                         current_time = time.time()
                         
                         # Check throttling
                         last_sent = sent_alerts.get(lug_id, 0)
                         if current_time - last_sent > ALERT_COOLDOWN:
                             broadcast_log_sync({
                                 "type": "CRITICAL",
                                 "message": f"Abandoned Luggage {item['id']}! {item['details']}",
                                 "timestamp": time.strftime("%H:%M:%S")
                             })
                             sent_alerts[lug_id] = current_time

        if frame_count % 3 == 0: # Broadcast objects every 3rd frame to save bandwidth
             broadcast_log_sync({
                 "type": "LIVE_FEED",
                 "objects": log_data, # log_data is now 'luggage_dashboard_data' which contains all objects
                 "timestamp": time.strftime("%H:%M:%S")
             })
             
        # Calculate Dynamic FPS
        elapsed = time.time() - start_time
        current_fps = 1.0 / elapsed if elapsed > 0 else 30.0

        if frame_count % 30 == 0:
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
        cv2.imshow("SecureVision - Live Feed (BotSORT Enabled)", frame_bgr_out)
        
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
