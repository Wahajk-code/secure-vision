import sys
import os
import torch
import cv2
import time
import numpy as np

# Adjust path to import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_pipeline.real_layer1 import get_yolo_detections
from config import USE_CUDA

def verify_cuda():
    print(f"Checking CUDA availability: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device: {torch.cuda.get_device_name(0)}")
        print(f"Config 'USE_CUDA': {USE_CUDA}")
    else:
        print("CUDA NOT AVAILABLE!")

    # Create dummy frame
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    print("Running warmup inference...")
    try:
        start_time = time.time()
        # Should trigger model load
        get_yolo_detections(frame, 1)
        print(f"Warmup done in {time.time() - start_time:.4f}s")
        
        print("Running timed inference (FP16 enabled if CUDA)...")
        start_time = time.time()
        get_yolo_detections(frame, 2)
        end_time = time.time()
        print(f"Inference time: {end_time - start_time:.4f}s")
        print("SUCCESS: Inference ran without errors.")

    except Exception as e:
        print(f"ERROR: Inference failed. {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_cuda()
