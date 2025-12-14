import cv2
import numpy as np
from config import SUSTAINED_DURATION_FRAMES, WEAPON_CLASSES
from core_pipeline.tracker_state import TrackerState
from core_pipeline.real_layer1 import get_yolo_detections
from utils.logger import setup_logger
from utils.stats_manager import StatsManager

logger = setup_logger(__name__)

class SecureVisionPipeline:
    def __init__(self, stream_id="default"):
        self.stream_id = stream_id
        # Initialize Tracker State per instance
        self.tracker_state = TrackerState()
        self.stats_manager = StatsManager()
        
        # State to track if we are in "Fight Detected" mode
        self.fight_detected_state = {
            'active': False,
            'frame_counter': 0,
            'involved_ids': []
        }

    def process_frame(self, frame, frame_number):
        """
        Main processing function for the pipeline instance.
        """
        # 1. Layer 1: Get Detections
        detections = get_yolo_detections(frame, frame_number)
        
        # 2. Update Tracker State
        self.tracker_state.update(detections, frame_number)
        
        # 3. Layer 2: Check for Potential Fight (DISABLED)
        # potential_fight_ids = check_for_potential_fight(self.tracker_state)
        
        # 3.5. Luggage Association
        self.tracker_state.assign_owners()
        
        status_message = "System Active"
        color = (0, 255, 0) # Green (RGB)
        
        # Handle persistent alert state
        if self.fight_detected_state['active']:
            status_message = f"FIGHT DETECTED! IDs: {self.fight_detected_state['involved_ids']}"
            color = (255, 0, 0) # Red (RGB)
            self.fight_detected_state['frame_counter'] -= 1
            if self.fight_detected_state['frame_counter'] <= 0:
                self.fight_detected_state['active'] = False

        # State Collection for Dashboard
        luggage_dashboard_data = []

        # Annotation
        from config import ABANDONED_DURATION_FRAMES, LUGGAGE_CLASSES
        
        # Get all updated tracks to access metadata like owner_id
        all_tracks = self.tracker_state.get_all_tracks()
        
        for det in detections:
            bbox = det['bbox']
            tid = det['track_id']
            cls = det['class']
            
            current_color = color # Default Green/Red based on Fight status
            label_suffix = ""
            
            # Weapon Detection Alert
            if cls in WEAPON_CLASSES:
                status_message = f"WEAPON DETECTED! ({cls.upper()})"
                current_color = (255, 0, 0) # Red (RGB)
                logger.critical(f"[{self.stream_id}] WEAPON DETECTED: {cls} at {bbox}")
                self.stats_manager.log_event("WEAPON", {"class": cls, "track_id": tid, "stream": self.stream_id})
            
            # Luggage Logic
            elif cls in LUGGAGE_CLASSES:
                track_info = all_tracks.get(tid)
                lug_status = "Normal"
                owner_info = "None"
                
                if track_info:
                    owner_id = track_info.get('owner_id')
                    abandoned_timer = track_info.get('abandoned_timer', 0)
                    
                    if owner_id is not None:
                        owner_info = f"Person {owner_id}"
                        # Draw line to owner
                        owner_track = all_tracks.get(owner_id)
                        if owner_track:
                            owner_centroid = owner_track['centroid'][-1]
                            lug_centroid = track_info['centroid'][-1]
                            cv2.line(frame, 
                                     (int(lug_centroid[0]), int(lug_centroid[1])), 
                                     (int(owner_centroid[0]), int(owner_centroid[1])), 
                                     (0, 255, 255), 2) # Cyan line (RGB: 0, 255, 255)
                            label_suffix = f" (Owner: {owner_id})"
                    
                    timer_display = "Safe"
                    if abandoned_timer > 0:
                        frames_left = ABANDONED_DURATION_FRAMES - abandoned_timer
                        if frames_left > 0:
                            timer_display = f"⚠️ {frames_left / 30:.1f}s"
                        else:
                            lug_status = "ABANDONED"
                            timer_display = "🚨 ALERT"
                            status_message = f"ABANDONED LUGGAGE! (ID: {tid})"
                            current_color = (255, 0, 0) # Red (RGB)
                            logger.warning(f"[{self.stream_id}] Abandoned Luggage ID {tid} detected!")
                            
                            if abandoned_timer % 30 == 0:
                                self.stats_manager.log_event("ABANDONED_LUGGAGE", {"track_id": tid, "stream": self.stream_id})
                            
                    # Add to dashboard data
                    luggage_dashboard_data.append({
                        "Luggage ID": tid,
                        "Type": cls,
                        "Owner": owner_info,
                        "Status": lug_status,
                        "Countdown": timer_display
                    })

            # Apply specific color if set (Weapon or Abandoned), else default
            box_color = current_color
            
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), box_color, 2)
            
            label = f"{cls} {tid}{label_suffix}"
            cv2.putText(frame, label, (int(bbox[0]), int(bbox[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, box_color, 2)
            
        # Draw Status Text
        cv2.putText(frame, status_message, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        return frame, status_message, luggage_dashboard_data

# Keep legacy function for backward compatibility
def process_frame(frame, frame_number):
    if not hasattr(process_frame, 'pipeline'):
        process_frame.pipeline = SecureVisionPipeline()
    return process_frame.pipeline.process_frame(frame, frame_number)
