import cv2
import numpy as np
import os
try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None
    print("Warning: ultralytics not installed. Real object detection will not work.")
from config import WEAPON_CLASSES, MODEL_PATH_LAYER1
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Singleton pattern or global variable to hold the model to avoid reloading every frame
_model = None

def get_model():
    global _model
    if YOLO is None:
        logger.error("Ultralytics not installed. Cannot load model.")
        return None

    if _model is None:
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', MODEL_PATH_LAYER1)
        if not os.path.exists(model_path):
            logger.error(f"Model not found at {model_path}. Please place 'best.pt' in securevision_core/models/")
            # Fallback to a standard model if specific one missing, or just fail?
            # For now let's try to load 'yolov8n.pt' as fallback if user hasn't put their model yet, 
            # BUT the user said they have a custom model with specific classes.
            # Using standard yolov8n might give wrong classes.
            # Better to raise error or return empty if file missing.
            raise FileNotFoundError(f"YOLO model file not found at {model_path}")
        
        logger.info(f"Loading YOLO model from {model_path}...")
        _model = YOLO(model_path)
    return _model

def get_yolo_detections(frame, frame_number):
    """
    Real Layer 1 output using YOLOv8+.
    
    Args:
        frame (np.array): Current video frame (RGB or BGR). Be mindful Ultralytics handles both but expects RGB usually or BGR->RGB auto.
                          OpenCV reads BGR. Streamlit sends RGB if we converted it, but pipeline.py says:
                          pipeline.py:74: frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                          pipeline.py:77: process_frame(frame_rgb, ...)
                          So 'frame' here is RGB.
        frame_number (int): Current frame number.
        
    Returns:
        list: List of dicts representing active tracks.
    """
    model = get_model()
    detections = []
    
    if model is None:
        return detections
    
    from config import WEAPON_CLASSES, MODEL_PATH_LAYER1, TRACKER_TYPE, USE_CUDA
    
    # Run tracking
    # persist=True ensures track IDs are maintained across frames
    device = 0 if USE_CUDA else 'cpu'
    # Use half precision (fp16) if using CUDA for speedup
    results = model.track(frame, persist=True, tracker=TRACKER_TYPE, device=device, verbose=False, conf=0.1, half=USE_CUDA)
    
    if not results:
        return detections
        
    r = results[0]
    
    if r.boxes:
        for box in r.boxes:
            # box.xyxy: [x1, y1, x2, y2]
            # box.id: track ID (if available)
            # box.cls: class index
            # box.conf: confidence
            
            coords = box.xyxy[0].cpu().numpy() # [x1, y1, x2, y2]
            x1, y1, x2, y2 = map(int, coords)
            
            cls_id = int(box.cls[0].item())
            cls_name = model.names[cls_id]
            
            # Track ID might be None if just detected and not tracked yet? 
            # Usually 'track' returns IDs. If None, we can assign -1 or skip.
            track_id = int(box.id[0].item()) if box.id is not None else -1
            
            centroid_x = (x1 + x2) / 2
            centroid_y = (y1 + y2) / 2
            
            detection = {
                'track_id': track_id,
                'class': cls_name,
                'bbox': [x1, y1, x2, y2],
                'centroid': [centroid_x, centroid_y],
                'confidence': float(box.conf[0].item())
            }
            
            detections.append(detection)
            
            # Additional logic for weapon detection logging handled in pipeline.py
            
    return detections
