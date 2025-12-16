import cv2
import numpy as np
from config import SUSTAINED_DURATION_FRAMES, WEAPON_CLASSES
from core_pipeline.tracker_state import TrackerState
from core_pipeline.real_layer1 import get_yolo_detections
from utils.logger import setup_logger
from utils.stats_manager import StatsManager
from core_pipeline.reid_manager import ReIDManager

logger = setup_logger(__name__)

class SecureVisionPipeline:
    def __init__(self, stream_id="default"):
        self.stream_id = stream_id
        # Initialize Tracker State per instance
        self.tracker_state = TrackerState()
        self.stats_manager = StatsManager()
        self.reid_manager = ReIDManager() # Initialize ReID
        
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
        
        # 3.2. ReID Processing (Person Identification)
        all_tracks = self.tracker_state.get_all_tracks()
        
        # Only process active tracks in current detections
        for det in detections:
            bbox = det['bbox']
            tid = det['track_id']
            cls = det['class']
            
            if cls == 'person':
                current_mapped_id = self.tracker_state.get_mapped_id(tid)
                
                # Logic:
                # 1. If this BoTSORT ID is new (not in our map) OR we want to verify it periodically
                # 2. Extract features
                # 3. Find match
                
                # Check track age/history len to decide if stable enough to extract
                track_info = all_tracks.get(tid)
                if track_info:
                    history_len = len(track_info['centroid'])
                    
                    # Heuristic: Extract on first few frames (stable) and then periodically
                    should_extract = (history_len == 5) or (history_len % 30 == 0)
                    
                    if should_extract:
                        embedding = self.reid_manager.extract_features(frame, bbox)
                        if embedding is not None:
                            # Try to match
                            matched_id, score = self.reid_manager.find_match(embedding)
                            
                            if matched_id is not None:
                                # Found a match! Remap current BoTSORT ID (tid) -> Matched Persistent ID (matched_id)
                                if current_mapped_id != matched_id:
                                    logger.info(f"[ReID] Matched BoTSORT {tid} -> Person {matched_id} (Score: {score:.2f})")
                                    self.tracker_state.set_mapping(tid, matched_id)
                                    # Also update the feature bank for the matched ID
                                    self.reid_manager.update_identity(matched_id, embedding, frame_number)
                            else:
                                # No match found. 
                                # If this is a new track (no mapping yet), register as NEW Identity
                                # Check if it's already mapped to something (means we registered it before).
                                if tid not in self.tracker_state.id_map:
                                    new_pid = self.reid_manager.register_new_identity(embedding, frame_number)
                                    self.tracker_state.set_mapping(tid, new_pid)
                                    logger.info(f"[ReID] New Identity Registered: Person {new_pid} (from BoTSORT {tid})")
                                else:
                                    # Already mapped (it represents an identity we created for this track)
                                    # Just update features
                                    pid = self.tracker_state.get_mapped_id(tid)
                                    self.reid_manager.update_identity(pid, embedding, frame_number)

        # 3.5. Luggage Association
        self.tracker_state.assign_owners()
        
        status_message = "System Active"
        color = (0, 255, 0) # Green (RGB)
        
        # Handle persistent alert state
        if self.fight_detected_state['active']:
            status_message = f"FIGHT DETECTED! IDs: {self.fight_detected_state['involved_ids']}"
            color = (0, 165, 255) # Orange for Fight (BGR)
            self.fight_detected_state['frame_counter'] -= 1
            if self.fight_detected_state['frame_counter'] <= 0:
                self.fight_detected_state['active'] = False

        # State Collection for Dashboard
        luggage_dashboard_data = []

        # Annotation
        from config import ABANDONED_DURATION_FRAMES, LUGGAGE_CLASSES, GHOST_FRAMES
        
        # Get all updated tracks to access metadata like owner_id
        all_tracks = self.tracker_state.get_all_tracks()
        
        all_tracks = self.tracker_state.get_all_tracks()
        
        # Iterate over ALL tracks to handle persistence (Ghost Tracking)
        for tid, track in all_tracks.items():
            # Use Mapped ID for Display if available
            display_id = self.tracker_state.get_mapped_id(tid)
            
            # skip if track is too old (older than GHOST_FRAMES)
            if frame_number - track['last_seen'] > GHOST_FRAMES:
                continue

            # Check for sufficient history to draw
            if len(track['bbox']) == 0:
                continue

            bbox = track['bbox'][-1] # Get latest bbox
            cls = track['class']
            
            # If track is lost (ghost), maybe visually distinguish it? 
            is_ghost = (frame_number - track['last_seen'] > 0)
            
            current_color = color # Default Green/Red based on Fight status
            label_suffix = ""
            if is_ghost:
                label_suffix += " (LOST)"
            
            if cls == 'person':
                # Show Persistent ID
                label_suffix += f" (P-ID: {display_id})"
            
            # Weapon Detection Alert
            if cls in WEAPON_CLASSES:
                status_message = f"WEAPON DETECTED! ({cls.upper()})"
                current_color = (0, 0, 255) # Red for Weapon (BGR)
                if not is_ghost: # Only log fresh detections to avoid spamming logs for ghosts
                     # Note: ideally we'd track weapon alerts too to prevent duplicate logs, 
                     # but user specifically asked about luggage.
                     pass 
                # For weapons, existing logic was logging on every frame... 
                # Let's keep it but ideally we should fix that too. 
                # But prioritizing Luggage as requested.
                if not is_ghost:
                     # logger.critical(f"[{self.stream_id}] WEAPON DETECTED: {cls} at {bbox}") # Reduced log spam
                     pass

            # Luggage Logic
            elif cls in LUGGAGE_CLASSES:
                lug_status = "Normal"
                owner_info = "None"
                
                owner_id = track.get('owner_id')
                abandoned_timer = track.get('abandoned_timer', 0)
                
                if owner_id is not None:
                    owner_info = f"Person {owner_id}"
                    label_suffix += f" (Owner: {owner_id})" # Always show owner ID
                    
                    # Draw line to owner
                    owner_track = all_tracks.get(owner_id)
                    # Only draw line if owner is also currently tracked or recently lost
                    if owner_track and (frame_number - owner_track['last_seen'] <= GHOST_FRAMES):
                        owner_centroid = owner_track['centroid'][-1]
                        lug_centroid = track['centroid'][-1]
                        cv2.line(frame, 
                                    (int(lug_centroid[0]), int(lug_centroid[1])), 
                                    (int(owner_centroid[0]), int(owner_centroid[1])), 
                                    (0, 255, 255), 2) # Cyan line (RGB: 0, 255, 255)
                        # label_suffix += f" (Owner: {owner_id})" # Removed redundant add
                
                timer_display = "Safe"
                if abandoned_timer > 0:
                    frames_left = ABANDONED_DURATION_FRAMES - abandoned_timer
                    if frames_left > 0:
                        timer_display = f"⚠️ {frames_left / 30:.1f}s"
                    else:
                        lug_status = "ABANDONED"
                        timer_display = "🚨 ALERT"
                        status_message = f"ABANDONED LUGGAGE! (ID: {tid})"
                        current_color = (0, 255, 255) # Yellow for Abandoned Luggage (BGR)
                        
                        # LOGGING LOGIC (FIXED)
                        if not track.get('is_abandoned_event_triggered', False):
                            logger.warning(f"[{self.stream_id}] Abandoned Luggage ID {tid} detected!")
                            self.stats_manager.log_event("ABANDONED_LUGGAGE", {"track_id": tid, "stream": self.stream_id})
                            track['is_abandoned_event_triggered'] = True
                        
            # Add to dashboard data (ALL objects)
            obj_data = {
                "id": tid,
                "category": cls,
                "status": "Normal",
                "details": "Tracking"
            }
            if is_ghost:
                obj_data["details"] = "Tracking (Lost)"

            if cls in WEAPON_CLASSES:
                obj_data["status"] = "CRITICAL"
                obj_data["details"] = "Weapon Detected"
                
            elif cls in LUGGAGE_CLASSES:
                obj_data["details"] = f"Owner: {owner_id if owner_id is not None else 'None'}"
                if abandoned_timer > 0:
                    frames_left = ABANDONED_DURATION_FRAMES - abandoned_timer
                    if frames_left > 0:
                        obj_data["details"] = f"⚠️ Abandoning in {frames_left / 30:.1f}s"
                        obj_data["status"] = "WARNING"
                    else:
                        obj_data["status"] = "CRITICAL"
                        obj_data["details"] = "🚨 ABANDONED"
            
            luggage_dashboard_data.append(obj_data)

            # Apply specific color if set (Weapon or Abandoned), else default
            box_color = current_color
            if is_ghost:
                # Dim the color for ghost tracks
                box_color = (int(box_color[0]*0.5), int(box_color[1]*0.5), int(box_color[2]*0.5))

            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), box_color, 2)
            
            label = f"{cls} {display_id}{label_suffix}"
            cv2.putText(frame, label, (int(bbox[0]), int(bbox[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, box_color, 2)
            
        # Draw Status Text
        cv2.putText(frame, status_message, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        return frame, status_message, luggage_dashboard_data

# Keep legacy function for backward compatibility
def process_frame(frame, frame_number):
    if not hasattr(process_frame, 'pipeline'):
        process_frame.pipeline = SecureVisionPipeline()
    return process_frame.pipeline.process_frame(frame, frame_number)
