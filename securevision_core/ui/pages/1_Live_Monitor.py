import streamlit as st
import cv2
import time
import os
import sys

# Add parent directory to path to import core modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from config import VIDEO_PATH
from core_pipeline.pipeline import SecureVisionPipeline
from utils.logger import setup_logger

# Setup logger
logger = setup_logger()

st.set_page_config(page_title="Live Monitor", page_icon="📹", layout="wide")

st.title("📹 Live Surveillance Monitor")

# Layout
col_videos, col_logs = st.columns([0.35, 0.65])

def run_monitor():
    # 1. Setup Single Stream (Multi-stream support is inherent in pipeline class if needed)
    if not os.path.exists(VIDEO_PATH):
        st.error(f"Video file not found at: {VIDEO_PATH}")
        return

    # Use session state to persist pipeline across reruns if needed, 
    # but for video loop usually we just run inside the main loop.
    
    cap = cv2.VideoCapture(VIDEO_PATH)
    pipeline = SecureVisionPipeline(stream_id="main_stream")
    
    st.sidebar.text(f"Source: {os.path.basename(VIDEO_PATH)}")
    st.sidebar.markdown("---")
    st.sidebar.info("**Legend**")
    st.sidebar.markdown("🟢 **Normal Object** (Green)")
    st.sidebar.markdown("🔴 **Weapon / Abandoned** (Red)")
    st.sidebar.markdown("🔵 **Owner Link** (Cyan/Teal)")

    with col_videos:
        st.subheader("Live Feed")
        video_placeholder = st.empty()

    with col_logs:
        st.header("Event Log")
        log_placeholder = st.empty()


    frame_count = 0
    fps = 0
    prev_time = time.time()
    
    # We use a button to stop the stream to allow visiting other pages cleanly
    stop_button = st.sidebar.button("Stop Stream")
    
    while not stop_button:
        frame_count += 1
        
        if not cap.isOpened():
            st.warning("Video stream closed.")
            break
            
        ret, frame = cap.read()
        if not ret:
            # Loop video
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            # If still no frame, break
            if not ret: break
        
        if ret:
            # Resize to 640x640 as requested for performance
            frame = cv2.resize(frame, (640, 640))

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Run pipeline
            annotated_frame, status, luggage_data = pipeline.process_frame(frame_rgb, frame_count)
            
            # Calculate FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time
            
            # Draw FPS on top right
            # Frame width is 640. Top right approx (520, 30)
            cv2.putText(annotated_frame, f"FPS: {int(fps)}", (520, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Update placeholder
            # Width set to 500 for smaller UI footprint as requested
            video_placeholder.image(annotated_frame, channels="RGB", width=500)

            # Update Luggage Log Table
            with log_placeholder.container():
                st.subheader("🎒 Luggage Monitor")
                if luggage_data:
                    st.dataframe(luggage_data, hide_index=True, use_container_width=True)
                else:
                    st.info("No luggage detected.")
        
        # Log Logic (kept minimal or removed as requested)
        # try:
        #    ...
        # except: pass

        
        # time.sleep(0.01) # Removed for MAX FPS
        pass

    cap.release()
    st.write("Stream stopped.")

if __name__ == "__main__":
    run_monitor()
