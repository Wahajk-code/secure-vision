
import cv2
import threading
import uvicorn
import time
import asyncio
import os
import signal
import sys
from api.main import app, broadcast_log_sync
from config import VIDEO_PATH, PROCESSING_WIDTH, LUGGAGE_CLASSES
from core_pipeline.pipeline import SecureVisionPipeline
from utils.logger import setup_logger

# Setup Logger
logger = setup_logger()

# Global Flag for Graceful Shutdown
running = True

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
    if not os.path.exists(VIDEO_PATH):
        logger.error(f"Video file not found: {VIDEO_PATH}")
        return

    cap = cv2.VideoCapture(VIDEO_PATH)
    pipeline = SecureVisionPipeline(stream_id="desktop_stream")
    frame_count = 0
    
    logger.info(f"Opening Native Video Window for: {os.path.basename(VIDEO_PATH)}")
    logger.info("Press 'Q' in the video window to quit.")

    while running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            logger.info("Video ended. Looping...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            # Reset sent alerts on loop if desired, or keep them to avoid re-spamming on loop
            # sent_alerts.clear() 
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
        
        # Run Pipeline
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
    cap.release()
    cv2.destroyAllWindows()
    logger.info("System Shutdown Complete.")
    sys.exit(0)

if __name__ == "__main__":
    main()
