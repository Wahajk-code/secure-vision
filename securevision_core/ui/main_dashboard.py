import streamlit as st
import cv2
import numpy as np
import tempfile
import time
import sys
import io
import os
from config import VIDEO_PATH, PROCESSING_WIDTH, DISPLAY_WIDTH
from core_pipeline.pipeline import SecureVisionPipeline
from utils.logger import setup_logger

# Setup logger
logger = setup_logger()

st.set_page_config(page_title="SecureVision Dashboard", layout="wide")

st.title("SecureVision Final Defense 1 - Multi-Stream Core Pipeline")

# Layout
col_videos, col_logs = st.columns([3, 1])

def run_dashboard():
    # 1. Setup Single Stream
    if not os.path.exists(VIDEO_PATH):
        st.error(f"Video file not found at: {VIDEO_PATH}")
        return

    cap = cv2.VideoCapture(VIDEO_PATH)
    pipeline = SecureVisionPipeline(stream_id="main_stream")
    
    st.sidebar.text(f"Source: {os.path.basename(VIDEO_PATH)}")

    with col_videos:
        st.subheader("Live Feed")
        video_placeholder = st.empty()

    with col_logs:
        st.header("Event Log")
        log_placeholder = st.empty()

    frame_count = 0
    fps_placeholder = st.sidebar.empty()
    prev_time = time.time()
    
    while True:
        frame_count += 1
        
        # FPS Calculation
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time
        
        # Update FPS display every few frames to avoid flickering
        if frame_count % 5 == 0:
            fps_placeholder.metric("Pipeline FPS", f"{fps:.1f}")
            # logger.info(f"Current FPS: {fps:.1f}")
        
        if not cap.isOpened():
            st.warning("Video stream closed.")
            break
            
        ret, frame = cap.read()
        if not ret:
            # Loop video
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            continue
        
        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # OPTIMIZATION: Resize to smaller width for processing (Logic Run)
            h, w = frame_rgb.shape[:2]
            aspect_ratio = h / w
            process_h = int(PROCESSING_WIDTH * aspect_ratio)
            frame_small = cv2.resize(frame_rgb, (PROCESSING_WIDTH, process_h))
            
            # Run pipeline on SMALL frame
            annotated_frame_small, status, _ = pipeline.process_frame(frame_small, frame_count)
            
            # RESIZE BACK UP for Display (so user sees big video)
            display_h = int(DISPLAY_WIDTH * aspect_ratio)
            annotated_frame_large = cv2.resize(annotated_frame_small, (DISPLAY_WIDTH, display_h))
            
            # Update placeholder with new dimensions
            video_placeholder.image(annotated_frame_large, channels="RGB", width=DISPLAY_WIDTH)
        
        # Update Log
        try:
            with open("securevision.log", "r") as f:
                lines = f.readlines()[-20:]
                log_text = "".join(lines)
                log_placeholder.text_area("System Logs", log_text, height=400, key=f"log_{frame_count}")
        except FileNotFoundError:
            pass
        
        time.sleep(0.01)

if __name__ == "__main__":
    run_dashboard()
