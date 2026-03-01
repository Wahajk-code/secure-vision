import cv2
import numpy as np
import os
try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None
    print("Warning: ultralytics not installed. Real object detection will not work.")
from config import WEAPON_CLASSES
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Storage for both models
_models = {'base': None, 'weapons': None}

def get_models():
    """Lazy load both models into VRAM to ensure we don't blow up init times."""
    global _models
    if YOLO is None:
        logger.error("Ultralytics not installed. Cannot load models.")
        return None

    from config import MODEL_BASE, MODEL_WEAPONS

    if _models['base'] is None:
        path_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', MODEL_BASE)
        if not os.path.exists(path_base):
            raise FileNotFoundError(f"YOLO Base model not found at {path_base}")
        logger.info(f"Loading Base model from {path_base}...")
        # Load with fp16 directly if possible? YOLO handles half precision in .track()
        _models['base'] = YOLO(path_base)

    if _models['weapons'] is None:
        path_weapons = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', MODEL_WEAPONS)
        if not os.path.exists(path_weapons):
             raise FileNotFoundError(f"YOLO Weapon model not found at {path_weapons}")
        logger.info(f"Loading Weapon model from {path_weapons}...")
        _models['weapons'] = YOLO(path_weapons)

    return _models

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
    models = get_models()
    detections = []
    
    if models is None:
        return detections
    
    from config import WEAPON_CLASSES, BASE_CLASSES, TRACKER_TYPE, USE_CUDA, CONFIDENCE_THRESHOLDS, MIN_CONFIDENCE
    
    device = 0 if USE_CUDA else 'cpu'

    # --- SEQUENTIAL BRUTE FORCE LOGIC ---
    # Run both models on every single frame to maximize accuracy
    # 1. Base Model (People, Luggage, Knives)
    results_base = models['base'].track(frame, persist=True, tracker=TRACKER_TYPE, device=device, verbose=False, conf=MIN_CONFIDENCE, half=USE_CUDA)
    
    # 2. Weapon Model (Guns, Rifles)
    results_weapons = models['weapons'].track(frame, persist=True, tracker=TRACKER_TYPE, device=device, verbose=False, conf=MIN_CONFIDENCE, half=USE_CUDA)
    
    # Helper function to process results
    def process_results(results, model_instance, valid_classes):
        if not results:
            return
            
        r = results[0]
        if r.boxes:
            for box in r.boxes:
                coords = box.xyxy[0].cpu().numpy() # [x1, y1, x2, y2]
                x1, y1, x2, y2 = map(int, coords)
                
                cls_id = int(box.cls[0].item())
                cls_name = model_instance.names[cls_id]
                
                # Model-Specific Class Gating
                if cls_name not in valid_classes:
                    continue
                    
                conf = float(box.conf[0].item())
                
                # Apply per-class confidence threshold filtering
                req_conf = CONFIDENCE_THRESHOLDS.get(cls_name, 0.4)
                if conf < req_conf:
                    continue
                
                # Track ID might be None if just detected and not tracked yet? 
                track_id = int(box.id[0].item()) if box.id is not None else -1
                
                centroid_x = (x1 + x2) / 2
                centroid_y = (y1 + y2) / 2
                
                detection = {
                    'track_id': track_id,
                    'class': cls_name,
                    'bbox': [x1, y1, x2, y2],
                    'centroid': [centroid_x, centroid_y],
                    'confidence': conf
                }
                detections.append(detection)

    # Process both arrays
    process_results(results_base, models['base'], BASE_CLASSES)
    process_results(results_weapons, models['weapons'], WEAPON_CLASSES)
    
    return detections
