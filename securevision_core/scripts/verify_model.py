import cv2
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import VIDEO_PATH, WEAPON_CLASSES
try:
    from core_pipeline.real_layer1 import get_yolo_detections, get_model
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure ultralytics is installed: pip install ultralytics")
    sys.exit(1)

def verify():
    # 1. Load Model
    try:
        model = get_model()
        print("Model loaded successfully.")
        print(f"Model classes: {model.names}")
    except Exception as e:
        print(f"Failed to load model: {e}")
        sys.exit(1)

    video_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testvideos')
import cv2
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import VIDEO_PATH, WEAPON_CLASSES
try:
    from core_pipeline.real_layer1 import get_yolo_detections, get_model
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure ultralytics is installed: pip install ultralytics")
    sys.exit(1)

def verify():
    # 1. Load Model
    try:
        model = get_model()
        print("Model loaded successfully.")
        print(f"Model classes: {model.names}")
    except Exception as e:
        print(f"Failed to load model: {e}")
        sys.exit(1)

    video_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testvideos')
    video_files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
    
    if not video_files:
        print("No video files found in testvideos directory.")
        return

    video_file = 'test2.mp4'
    video_path = os.path.join(video_dir, video_file)
    print(f"\n--- DEBUG SCAN: {video_file} ---")
    
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame_count += 1
        if frame_count > 100: break 
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detections = get_yolo_detections(frame_rgb, frame_count)
        
        if detections:
            print(f"Frame {frame_count}:")
            for d in detections:
                print(f"  - {d['class']} ({d.get('confidence',0):.2f})")

    cap.release()

if __name__ == "__main__":
    verify()
