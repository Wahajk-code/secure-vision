import cloudinary
import cloudinary.uploader
import os
import threading
import cv2
import time
from utils.logger import setup_logger
from api.main import broadcast_log_sync

logger = setup_logger()

# Configure Cloudinary using environment variables or hardcoded values
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dxu84g4p6"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "746356743958933"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "N7yJns6wD_yB10E1v73f7mIFXU4")
)

def _upload_worker(frame, description, timestamp):
    """
    Background worker that saves the frame to disk, uploads it to Cloudinary,
    and then broadcasts the resulting secure URL to the React frontend.
    """
    try:
        # Create a temporary file
        temp_filename = f"temp_evidence_{int(time.time())}.jpg"
        cv2.imwrite(temp_filename, frame)
        
        logger.info(f"[Cloudinary] Starting background upload for '{description}'...")
        
        # Upload
        response = cloudinary.uploader.upload(
            temp_filename, 
            folder="securevision_evidence",
            resource_type="image"
        )
        
        secure_url = response.get('secure_url')
        logger.info(f"[Cloudinary] Upload success! URL: {secure_url}")
        
        # Cleanup local file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        
        # Broadcast the image URL to the React Dashboard
        broadcast_log_sync({
            "type": "CRITICAL_IMAGE",
            "image_url": secure_url,
            "message": description,
            "timestamp": timestamp
        })
        
    except Exception as e:
        logger.error(f"[Cloudinary] Upload failed: {e}")

def upload_image_async(frame, description, timestamp):
    """
    Spawns a background thread to upload a critical frame to Cloudinary
    without blocking the real-time AI computer vision loop.
    """
    # Convert RGB frame back to BGR for correct OpenCV saving colors 
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    thread = threading.Thread(
        target=_upload_worker, 
        args=(frame_bgr, description, timestamp), 
        daemon=True
    )
    thread.start()
