import streamlit as st
import cv2
import numpy as np
import tempfile
import time
import sys
import io
import os
from config import VIDEO_PATH
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
    
    while True:
        frame_count += 1
        
        if not cap.isOpened():
            st.warning("Video stream closed.")
            break
            
        ret, frame = cap.read()
        if not ret:
            # Loop video
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
        
        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Run pipeline
            annotated_frame, status = pipeline.process_frame(frame_rgb, frame_count)
            
            # Resize frame: Increase width and height by 100px
            h, w = annotated_frame.shape[:2]
            new_w = w + 100
            new_h = h + 100
            annotated_frame = cv2.resize(annotated_frame, (new_w, new_h))
            
            # Update placeholder with new dimensions
            video_placeholder.image(annotated_frame, channels="RGB", width=new_w)
        
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
