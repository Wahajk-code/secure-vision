import numpy as np
from config import FRAME_RATE

def get_yolo_detections(frame, frame_number):
    """
    Simulates Layer 1 output (YOLOv11 + BoTSORT).
    
    Args:
        frame (np.array): Current video frame.
        frame_number (int): Current frame number.
        
    Returns:
        list: List of dicts representing active tracks.
    """
    detections = []
    
    # Simulate two people (Track IDs 12 and 15)
    # They approach each other, interact (fight), and then maybe separate or stay close.
    
    # Frame ranges for simulation:
    # 0-50: Walking towards each other
    # 50-150: Close proximity (Potential Fight Trigger)
    # 150+: Separating
    
    # Image dimensions (assuming 1920x1080 for mock coordinates)
    width, height = 1920, 1080
    
    # Person 1 (ID 12)
    p1_start = np.array([400, 500])
    p1_meet = np.array([900, 500])
    
    # Person 2 (ID 15)
    p2_start = np.array([1500, 500])
    p2_meet = np.array([950, 500]) # 50 pixels apart (approx 0.5m if 1m=100px)
    
    if frame_number < 50:
        alpha = frame_number / 50.0
        p1_pos = (1 - alpha) * p1_start + alpha * p1_meet
        p2_pos = (1 - alpha) * p2_start + alpha * p2_meet
    elif frame_number < 150:
        # Jitter/Fighting movement
        p1_pos = p1_meet + np.random.randint(-20, 20, size=2)
        p2_pos = p2_meet + np.random.randint(-20, 20, size=2)
    else:
        # Separate
        alpha = (frame_number - 150) / 50.0
        if alpha > 1: alpha = 1
        p1_pos = (1 - alpha) * p1_meet + alpha * p1_start
        p2_pos = (1 - alpha) * p2_meet + alpha * p2_start

    # Create detection objects
    # BBox format: [x1, y1, x2, y2]
    # Assume size 100x200
    
    # Track 12
    detections.append({
        'track_id': 12,
        'class': 'person',
        'bbox': [p1_pos[0]-50, p1_pos[1]-100, p1_pos[0]+50, p1_pos[1]+100],
        'centroid': p1_pos.tolist()
    })
    
    # Track 15
    detections.append({
        'track_id': 15,
        'class': 'person',
        'bbox': [p2_pos[0]-50, p2_pos[1]-100, p2_pos[0]+50, p2_pos[1]+100],
        'centroid': p2_pos.tolist()
    })

    # Simulate Gun (Weapon Detection)
    # Person 1 pulls a gun during the fight (frames 100-140)
    if 100 <= frame_number <= 140:
        gun_pos = p1_pos + np.array([40, 10]) # Near right hand
        detections.append({
            'track_id': 99, # Unique ID for the object
            'class': 'gun',
            'bbox': [gun_pos[0]-10, gun_pos[1]-10, gun_pos[0]+10, gun_pos[1]+10],
            'centroid': gun_pos.tolist()
        })
    
    return detections
