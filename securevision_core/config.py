import os

# Video Configuration
# VIDEO_PATH = 'overridden_by_ui_discovery' 
VIDEO_PATH = os.path.join(os.path.dirname(__file__), 'testvideos', 'test-ismaeel2.mp4')
FRAME_RATE = 30

# Fight Detection Thresholds
PROXIMITY_THRESHOLD_METERS = 1.0  # Meters
SUSTAINED_DURATION_FRAMES = 60    # ~2 seconds at 30 FPS

# Model Paths (Mock)
MODEL_PATH_LAYER1 = 'weaponDetection.pt'
MODEL_PATH_LAYER3 = 'fight_classifier.pt'

# Weapon Detection Classes
# Standard YOLO classes or custom trained classes for weapons
WEAPON_CLASSES = ['gun', 'knife']
LUGGAGE_CLASSES = ['backpack', 'handbag', 'suitcase']

# Luggage Abandonment Logic
ABANDONED_DURATION_FRAMES = 150  # 5 seconds at 30 FPS
LUGGAGE_PROXIMITY_THRESHOLD = 200 # Pixels (approx 1-2 meters depending on depth)

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
