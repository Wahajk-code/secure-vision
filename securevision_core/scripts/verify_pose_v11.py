
import cv2
import numpy as np
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core_pipeline.pose_filter import PoseKeypointFilter

def test_pose_model():
    print("Initializing PoseKeypointFilter (this should trigger YOLO11n-pose download)...")
    try:
        pose_filter = PoseKeypointFilter(model_name='yolo11n-pose.pt')
    except Exception as e:
        print(f"FAILED to initialize filter: {e}")
        return

    if pose_filter.model is None:
        print("Model failed to load (check warnings above).")
        return

    print("Model loaded successfully.")
    
    # Create a dummy image (simulating a crop)
    print("Running dummy inference...")
    dummy_frame = np.zeros((200, 100, 3), dtype=np.uint8)
    # Draw a stick figure so it detects something (maybe) or just check it doesn't crash on empty/noise
    # Actually YOLO might not detect anything on black, but we just want to verify Inference RUNS.
    
    # To test detection we need a real image, but to test compatibility/loading we just need to run it.
    score = pose_filter.get_arm_velocity_score(dummy_frame, 1, [0, 0, 100, 200])
    
    print(f"Inference run complete. Score: {score}")
    print("SUCCESS: YOLO11n-pose is ready.")

if __name__ == "__main__":
    test_pose_model()
