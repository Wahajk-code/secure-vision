import cv2
import math
from config import SUSTAINED_DURATION_FRAMES, PROXIMITY_THRESHOLD_METERS, PROCESSING_WIDTH

# Heuristic: Pixel threshold for "Close Proximity"
# People interacting (fighting/hugging) are usually within this range
FIGHT_PROXIMITY_THRESHOLD_PIXELS = 150 # Reduced back to reasonable interaction distance

# Velocity Thresholds
VELOCITY_THRESHOLD_ACITVITY = 2.0 # Significant movement
VELOCITY_THRESHOLD_EXPLOSIVE = 5.0 # Very fast movement (immediate trigger)

# Import FightNet
from core_pipeline.fightnet_integration import run_fightnet
from core_pipeline.pose_filter import PoseKeypointFilter

class FightDetector:
    def __init__(self):
        # State to track potential fights
        # Key: tuple(id1, id2) (sorted)
        # Value: { 'start_frame': int, 'last_seen': int, 'status': 'MONITORING' | 'VERIFYING' | 'CONFIRMED' }
        self.active_pairs = {}
        
        # Debounce/Cleanup
        self.LOST_PAIR_THRESHOLD = 30 # If pair separates for 30 frames, reset
        self.VERIFY_INTERVAL = 5 # Check mock model every 5 frames if conditions met
        
        self.pose_filter = PoseKeypointFilter()
        self.POSE_ACTIVITY_THRESHOLD = 30.0 # Heuristic combination of velocity + contact
        
    def _calculate_body_velocity(self, track1, track2):
        """
        Calculates the average velocity (pixels/frame) of two bodies based on centroid history.
        """
        def get_v(track):
            history = track['centroid']
            if len(history) < 3: return 0.0 # Need at least 3 points for reliable speed
            # Distance between now and 3 frames ago
            c_now = history[-1]
            c_old = history[-3]
            dist = math.sqrt((c_now[0]-c_old[0])**2 + (c_now[1]-c_old[1])**2)
            return dist / 3.0 # pixels per frame
        
        v1 = get_v(track1)
        v2 = get_v(track2)
        return (v1 + v2) / 2.0  

    def process(self, tracks, frame_number, frame):
        """
        Returns: List of detected events.
        """
        current_people = []
        
        # 1. Filter for active People
        for tid, track in tracks.items():
            if track['class'] == 'person':
                if frame_number - track['last_seen'] < 5: 
                     if len(track['centroid']) > 0:
                        current_people.append((tid, track, track['centroid'][-1], track['bbox'][-1]))

        current_pair_keys = set()
        detected_fights = [] 

        # Naive O(N^2)
        for i in range(len(current_people)):
            for j in range(i + 1, len(current_people)):
                id1, track1, cen1, bbox1 = current_people[i]
                id2, track2, cen2, bbox2 = current_people[j]
                
                # Euclidean Distance
                dist = math.sqrt((cen1[0] - cen2[0])**2 + (cen1[1] - cen2[1])**2)
                
                if dist < FIGHT_PROXIMITY_THRESHOLD_PIXELS:
                    pair_key = tuple(sorted((id1, id2)))
                    current_pair_keys.add(pair_key)
                    
                    if pair_key not in self.active_pairs:
                        self.active_pairs[pair_key] = {
                            'start_frame': frame_number,
                            'last_seen': frame_number,
                            'status': 'MONITORING'
                        }
                    else:
                        self.active_pairs[pair_key]['last_seen'] = frame_number
                        
                        # Logic: Proximity + Velocity = Fight Candidate
                        body_velocity = self._calculate_body_velocity(track1, track2)
                        
                        # Trigger Conditions
                        is_candidate = False
                        
                        # A. Sustained Activity
                        duration = frame_number - self.active_pairs[pair_key]['start_frame']
                        if duration > 30 and body_velocity > VELOCITY_THRESHOLD_ACITVITY:
                            is_candidate = True
                            
                        # B. Explosive Movement (Immediate)
                        if body_velocity > VELOCITY_THRESHOLD_EXPLOSIVE:
                            is_candidate = True
                            
                        if is_candidate:
                            # Advanced Gate: Pose Verification
                            arm_score_1, kpts1 = self.pose_filter.get_arm_velocity_score(frame, id1, bbox1)
                            arm_score_2, kpts2 = self.pose_filter.get_arm_velocity_score(frame, id2, bbox2)
                            
                            if 'pose_buffer' not in self.active_pairs[pair_key]:
                                self.active_pairs[pair_key]['pose_buffer'] = []
                                
                            import numpy as np
                            frame_features = np.stack([kpts1, kpts2])
                            self.active_pairs[pair_key]['pose_buffer'].append(frame_features)
                            
                            if len(self.active_pairs[pair_key]['pose_buffer']) > 30:
                                self.active_pairs[pair_key]['pose_buffer'].pop(0)
                            
                            pose_activity = max(arm_score_1, arm_score_2)
                            
                            if pose_activity > self.POSE_ACTIVITY_THRESHOLD:
                                # Run Mock Model Verification
                                if len(self.active_pairs[pair_key]['pose_buffer']) >= 15:
                                    if self.active_pairs[pair_key]['status'] != 'CONFIRMED':
                                        result = run_fightnet(self.active_pairs[pair_key]['pose_buffer'])
                                        if result:
                                            self.active_pairs[pair_key]['status'] = 'CONFIRMED'
                                        else:
                                            self.active_pairs[pair_key]['status'] = 'WARNING'
                    
                    # Add to return list 
                    status = self.active_pairs[pair_key]['status']
                    pose_len = len(self.active_pairs[pair_key].get('pose_buffer', []))
                    if status == 'CONFIRMED' or pose_len > 0:
                        display_status = status if status == 'CONFIRMED' else 'WARNING'
                        detected_fights.append({
                            'ids': list(pair_key),
                            'status': display_status,
                            'distance': dist,
                            'timer': pose_len
                        })

        # Cleanup stale pairs
        keys_to_delete = []
        for pair_key, info in self.active_pairs.items():
            if frame_number - info['last_seen'] > self.LOST_PAIR_THRESHOLD:
                keys_to_delete.append(pair_key)
        
        for k in keys_to_delete:
            del self.active_pairs[k]

        return detected_fights


