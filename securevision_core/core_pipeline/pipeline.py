import cv2
import numpy as np
from config import SUSTAINED_DURATION_FRAMES, WEAPON_CLASSES
from core_pipeline.tracker_state import TrackerState
from core_pipeline.real_layer1 import get_yolo_detections
from utils.logger import setup_logger
from utils.stats_manager import StatsManager
from core_pipeline.reid_manager import ReIDManager
from core_pipeline.fight_detector import FightDetector

logger = setup_logger(__name__)

class SecureVisionPipeline:
    def __init__(self, stream_id="default"):
        self.stream_id = stream_id
        # Initialize Tracker State per instance
        self.tracker_state = TrackerState()
        self.stats_manager = StatsManager()
        self.reid_manager = ReIDManager() # Initialize ReID
        self.fight_detector = FightDetector() # Initialize Fight Detector
        self.recording_frames_left = 0 # Initialize recording state
        self.fight_snapshot_cooldown = 0 # Prevent taking thousands of screenshots for continuous fights
        self.alert_persistence = {} # {tid: {'status': ..., 'details': ..., 'color': ..., 'frames': 30}}

    def process_frame(self, frame, frame_number, capture_callback=None):
        """
        Main processing function for the pipeline instance.
        """
        # 1. Layer 1: Get Detections
        detections = get_yolo_detections(frame, frame_number)
        
        # 2. Update Tracker State
        self.tracker_state.update(detections, frame_number)
        
        # Decrement snapshot cooldown
        if self.fight_snapshot_cooldown > 0:
            self.fight_snapshot_cooldown -= 1
            
        # 3. Layer 2: Check for Fight
        fight_events = self.fight_detector.process(self.tracker_state.get_all_tracks(), frame_number, frame)
        
        # Map fight status to IDs for O(1) lookup during drawing
        # format: {id: {'status': 'WARNING'|'CONFIRMED', 'partner': id}}
        fight_status_map = {}
        for event in fight_events:
            id1, id2 = event['ids']
            status = event['status']
            timer = event.get('timer', 0)
            fight_status_map[id1] = {'status': status, 'partner': id2, 'timer': timer}
            fight_status_map[id2] = {'status': status, 'partner': id1, 'timer': timer}
            
            # Log critical fights
            if status == 'CONFIRMED':
                # Throttle logging if needed, or rely on StatsManager in detector?
                # For now let's just ensure we have global visibility
                logger.warning(f"[{self.stream_id}] CRITICAL: FIGHT DETECTED! IDs: {id1}-{id2}")
                # Start/Extend Recording only if cooldown has expired
                if self.fight_snapshot_cooldown == 0:
                    self.recording_frames_left = 1 # Take exactly 1 snapshot
                    self.fight_snapshot_cooldown = 150 # Wait 150 frames (5 seconds) before taking another snapshot of any fight
                    self._last_critical_reason = f"CRITICAL: FIGHT DETECTED! IDs: {id1}-{id2}"
                
        # 3.1. Frame Recording Logic
        if self.recording_frames_left > 0:
            import os
            # Ensure directory exists (can be moved to init usually, but safe here)
            capture_dir = os.path.join(os.path.dirname(__file__), '..', 'captures')
            os.makedirs(capture_dir, exist_ok=True)
            
            # Save Frame
            filename = os.path.join(capture_dir, f"critical_event_frame_{frame_number}.jpg")
            try:
                cv2.imwrite(filename, frame)
                if capture_callback and hasattr(self, '_last_critical_reason'):
                    capture_callback(filename, getattr(self, '_last_critical_reason', "CRITICAL EVENT"))
                # logger.info(f"Captured fight frame: {filename}") # Optional: Debug log
            except Exception as e:
                logger.error(f"Failed to save frame: {e}")
                
            self.recording_frames_left -= 1
            if self.recording_frames_left == 0:
                logger.info(f"[{self.stream_id}] Incident Recording Snapshot Saved.")
        
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
        
        # State Collection for Dashboard
        luggage_dashboard_data = []

        # Annotation
        from config import ABANDONED_DURATION_FRAMES, LUGGAGE_CLASSES, GHOST_FRAMES_WEAPON, GHOST_FRAMES_LUGGAGE, GHOST_FRAMES_PERSON
        
        # Get all updated tracks to access metadata like owner_id
        all_tracks = self.tracker_state.get_all_tracks()
        
        all_tracks = self.tracker_state.get_all_tracks()
        
        # Iterate over ALL tracks to handle persistence (Ghost Tracking)
        for tid, track in all_tracks.items():
            # Decrement persistence timer for this track if it exists
            if tid in self.alert_persistence:
                self.alert_persistence[tid]['frames'] -= 1
                if self.alert_persistence[tid]['frames'] <= 0:
                    del self.alert_persistence[tid]
            
            # Extract Class early for persistence rules
            cls = track['class']
            
            # Use Mapped ID for Display if available
            display_id = self.tracker_state.get_mapped_id(tid)
            
            # Determine class-specific persistence allowance
            if cls in WEAPON_CLASSES:
                ghost_thresh = GHOST_FRAMES_WEAPON
            elif cls in LUGGAGE_CLASSES:
                ghost_thresh = GHOST_FRAMES_LUGGAGE
            else:
                ghost_thresh = GHOST_FRAMES_PERSON
            
            # skip if track is too old AND we don't have an actively flashing persistent alert
            if (frame_number - track['last_seen'] > ghost_thresh) and (tid not in self.alert_persistence):
                continue

            # Check for sufficient history to draw
            if len(track['bbox']) == 0:
                continue

            bbox = track['bbox'][-1] # Get latest bbox
            
            # If track is lost (ghost), maybe visually distinguish it? 
            is_ghost = (frame_number - track['last_seen'] > 0)
            
            current_color = (0, 255, 0) # Global fallback color
            label_suffix = ""
            if is_ghost:
                label_suffix += " (LOST)"
            
            # Initialize obj_data early so all logic branches can update it
            obj_data = {
                "id": tid,
                "category": cls,
                "status": "Normal",
                "details": "Tracking"
            }
            if is_ghost:
                obj_data["details"] = "Tracking (Lost)"
            
            if cls == 'person':
                # Show Persistent ID
                label_suffix += f" (P-ID: {display_id})"
            
            # Weapon Detection Alert
            if cls in WEAPON_CLASSES:
                frames_seen = len(track['bbox'])
                
                # Debounce: Require at least 3 frames of tracking to confirm it's a real weapon and not a glitch
                if frames_seen >= 3:
                    current_color = (0, 0, 255) # Red for Weapon (BGR)
                    
                    # Flag as critical immediately
                    obj_data["status"] = "CRITICAL"
                    obj_data["details"] = "WEAPON"
                    
                    if not is_ghost and self.fight_snapshot_cooldown == 0:
                         self.recording_frames_left = 1
                         self.fight_snapshot_cooldown = 150 # 5 sec cooldown for all critical grabs
                         self._last_critical_reason = f"WEAPON DETECTED! ({cls.upper()})"
                else:
                    current_color = (0, 165, 255) # Orange for verification
                    obj_data["status"] = "WARNING"
                    obj_data["details"] = f"Verifying ({frames_seen}/3)"

            # Luggage Logic
            elif cls in LUGGAGE_CLASSES:
                lug_status = "Normal"
                owner_info = "None"
                
                owner_id = track.get('owner_id')
                abandoned_timer = track.get('abandoned_timer', 0)
                
                if owner_id is not None:
                    owner_info = f"Person {owner_id}"
                    label_suffix += f" (Owner: {owner_id})" # Always show owner ID
                
                timer_display = "Safe"
                if abandoned_timer > 0:
                    frames_left = ABANDONED_DURATION_FRAMES - abandoned_timer
                    if frames_left > 0:
                        timer_display = f"⚠️ {frames_left / 30:.1f}s"
                        obj_data["details"] = timer_display
                        obj_data["status"] = "WARNING"
                    else:
                        lug_status = "ABANDONED"
                        current_color = (0, 255, 255) # Yellow for Abandoned Luggage (BGR)
                        
                        obj_data["details"] = "🚨 ABANDONED"
                        obj_data["status"] = "CRITICAL"
                        
                        # LOGGING LOGIC (FIXED)
                        if not track.get('is_abandoned_event_triggered', False):
                            logger.warning(f"[{self.stream_id}] Abandoned Luggage ID {tid} detected!")
                            self.stats_manager.log_event("ABANDONED_LUGGAGE", {"track_id": tid, "stream": self.stream_id})
                            track['is_abandoned_event_triggered'] = True
                            
                        # Grab frame
                            if self.fight_snapshot_cooldown == 0:
                                self.recording_frames_left = 1
                                self.fight_snapshot_cooldown = 150
                                self._last_critical_reason = f"ABANDONED LUGGAGE! (ID: {tid})"
            
            # Fight Status Override
            if tid in fight_status_map:
                f_info = fight_status_map[tid]
                timer_val = f_info.get('timer', 0)
                if f_info['status'] == 'CONFIRMED':
                    obj_data['status'] = 'CRITICAL'
                    obj_data['details'] = f"FIGHTING with {f_info['partner']}"
                    current_color = (139, 0, 0)  # Dark Blue in BGR
                    label_suffix += " (FIGHT!)"
                elif f_info['status'] == 'WARNING':
                     obj_data['status'] = 'WARNING'
                     obj_data['details'] = f"Analyzing {timer_val}/30 (P{f_info['partner']})"
                     current_color = (0, 165, 255)
                     label_suffix += f" (Wait: {timer_val}/30)"

            # Apply / Save Persistence
            if obj_data['status'] in ['WARNING', 'CRITICAL']:
                if not is_ghost:
                    # Save to persistence cache only if actively tracked
                    self.alert_persistence[tid] = {
                        'status': obj_data['status'],
                        'details': obj_data['details'],
                        'color': current_color,
                        'frames': 30 # Hold this alert visually for 1 second minimum
                    }
                elif tid in self.alert_persistence:
                    # Clear persistence immediately if object is definitively lost
                    del self.alert_persistence[tid]
            elif tid in self.alert_persistence:
                # Restore from persistence cache if current frame didn't trigger
                p = self.alert_persistence[tid]
                obj_data['status'] = p['status']
                obj_data['details'] = p['details']
                current_color = p['color']

            if cls in WEAPON_CLASSES:
                pass # Already handled above
                
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
                
            # ENFORCEMENT: ONLY DRAW 3 SPECIFIC BOUNDING BOXES
            # Abandoned Luggage = Yellow (0, 255, 255)
            # Confirmed Weapon = Red (0, 0, 255) 
            # Confirmed Fight = Dark Blue (139, 0, 0)
            
            should_draw = False
            if obj_data['category'] in LUGGAGE_CLASSES and obj_data['status'] == 'CRITICAL':
                should_draw = True # Abandoned Luggage
            elif obj_data['category'] in WEAPON_CLASSES and obj_data['status'] == 'CRITICAL':
                should_draw = True # Confirmed Weapon
            elif obj_data['category'] == 'person' and 'FIGHTING' in obj_data['details']:
                should_draw = True # Confirmed Fight
                
            if should_draw:
                cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), box_color, 2)
                
                label = f"{cls} {display_id}{label_suffix}"
                cv2.putText(frame, label, (int(bbox[0]), int(bbox[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, box_color, 2)

        return frame, "", luggage_dashboard_data

# Keep legacy function for backward compatibility
def process_frame(frame, frame_number, capture_callback=None):
    if not hasattr(process_frame, 'pipeline'):
        process_frame.pipeline = SecureVisionPipeline()
    return process_frame.pipeline.process_frame(frame, frame_number, capture_callback=capture_callback)
