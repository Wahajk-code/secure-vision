import os
from dotenv import load_dotenv

# Load environment variables (Cloudinary DB, etc)
load_dotenv()

# Video Configuration
# VIDEO_PATH = 'overridden_by_ui_discovery' 
VIDEO_PATH = os.path.join(os.path.dirname(__file__), 'testvideos', 'fight-test1.mp4')
FRAME_RATE = 30
PROCESSING_WIDTH = 640
DISPLAY_WIDTH = 1000

# Fight Detection Thresholds
PROXIMITY_THRESHOLD_METERS = 1.0  # Meters
SUSTAINED_DURATION_FRAMES = 60    # ~2 seconds at 30 FPS

# Model Paths (Mock & Real)
MODEL_BASE = 'weapon_detection2.pt'
MODEL_WEAPONS = 'weapon_detection4.pt'
MODEL_PATH_LAYER3 = 'fight_classifier.pt'

# Tracker Configuration
TRACKER_TYPE = 'botsort.yaml' # Heavy ReID CNN enabled
USE_CUDA = True # Set to True if NVIDIA GPU is available

# Detection Classes
# Base Classes (Using custom weapon_detection2 now instead of COCO YOLO)
BASE_CLASSES = ['person', 'suitcase', 'handbag', 'backpack']

# Custom Trained Classes (Weapon Model)
WEAPON_CLASSES = ['Gun', 'rifle', 'gun'] # Adding both cases to be safe
LUGGAGE_CLASSES = ['backpack', 'handbag', 'suitcase']

# Per-Class Confidence Thresholds
CONFIDENCE_THRESHOLDS = {
    'Gun': 0.40,      # Increased to reduce false positives
    'gun': 0.40,
    'knife': 0.05,    # High sensitivity for knives
    'rifle': 0.40,    # Increased to reduce false positives
    'backpack': 0.10, # Lowered threshold for consistent bag detection
    'handbag': 0.10,
    'suitcase': 0.10,
    'person': 0.35    # Standard sensitivity for people
}
MIN_CONFIDENCE = 0.15 # The baseline threshold passed to YOLO

# Luggage Abandonment Logic
ABANDONED_DURATION_FRAMES = 150  # 5 seconds at 30 FPS
LUGGAGE_PROXIMITY_THRESHOLD = 200 # Pixels (approx 1-2 meters depending on depth)
GHOST_FRAMES_WEAPON = 0    # Instantly drop weapons to avoid false positive blips
GHOST_FRAMES_LUGGAGE = 30  # Keep luggage boxes for 1 second if occluded by pedestrians
GHOST_FRAMES_PERSON = 15   # Keep people for 0.5 seconds

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "postgres", # Assumed default from user context
    "password": "wahaj123",
    "dbname": "fyp"
}

# Logging
LOG_FILE_PATH = 'securevision.log'
