import numpy as np
from collections import deque
from config import SUSTAINED_DURATION_FRAMES

class TrackerState:
    """
    Maintains the state of BoTSORT Track IDs and their kinematic history.
    """
    def __init__(self, history_len=SUSTAINED_DURATION_FRAMES + 10):
        self.tracks = {}  # Dict[track_id, {'bbox': [], 'centroid': [], 'class': str}]
        self.history_len = history_len
        self.frame_count = 0
        
        # ID Mapping: BoTSORT ID (int) -> Persistent Person ID (int)
        # This allows us to remap a new BoTSORT track to an old Person ID if ReID matches.
        self.id_map = {} 

    def get_mapped_id(self, botsort_id):
        """Returns the persistent ID for a given BoTSORT ID, or the ID itself if no mapping exists."""
        return self.id_map.get(botsort_id, botsort_id)
    
    def set_mapping(self, botsort_id, persistent_id):
        """Maps a (likely new) BoTSORT ID to an existing Persistent ID."""
        self.id_map[botsort_id] = persistent_id

    def assign_owners(self):
        """
        Associates luggage (backpack, handbag, suitcase) with the closest person.
        Updates 'owner_id' and 'abandoned_timer' for each luggage track.
        """
        from config import LUGGAGE_CLASSES, LUGGAGE_PROXIMITY_THRESHOLD

        persons = {} # Map Persistent ID to centroid
        luggage = []

        # Separate people and luggage
        for tid, track in self.tracks.items():
            # Check if track was updated recently (e.g. within last 5 frames) to be considered 'active'
            if self.frame_count - track['last_seen'] > 10:
                continue

            # RESOLVE ID
            effective_id = self.get_mapped_id(tid)

            if track['class'] == 'person':
                persons[effective_id] = track['centroid'][-1]
            elif track['class'] in LUGGAGE_CLASSES:
                luggage.append(tid)

        for lug_id in luggage:
            lug_track = self.tracks[lug_id]
            lug_centroid = np.array(lug_track['centroid'][-1])
            
            # Initialize metadata if missing
            if 'abandoned_timer' not in lug_track:
                lug_track['abandoned_timer'] = 0
            if 'owner_id' not in lug_track:
                lug_track['owner_id'] = None
            if 'is_abandoned_event_triggered' not in lug_track:
                lug_track['is_abandoned_event_triggered'] = False

            current_owner_id = lug_track['owner_id']
            owner_nearby = False

            # Valid Owner Check Strategy:
            # 1. If we have an owner, ONLY check against that owner (using Persistent ID).
            # 2. If we don't have an owner, find the closest person to assign.

            if current_owner_id is not None:
                # Check if specific owner is present and close
                # current_owner_id is ALREADY a persistent ID (saved previously)
                if current_owner_id in persons:
                    owner_centroid = np.array(persons[current_owner_id])
                    dist = np.linalg.norm(lug_centroid - owner_centroid)
                    
                    if dist < LUGGAGE_PROXIMITY_THRESHOLD:
                        owner_nearby = True
                
                # Note: If owner is NOT in 'persons' (left the scene), owner_nearby remains False
                
            else:
                # No owner assigned yet, try to find one
                closest_person_id = None
                min_dist = float('inf')

                for pid, p_centroid in persons.items():
                    dist = np.linalg.norm(lug_centroid - np.array(p_centroid))
                    if dist < min_dist:
                        min_dist = dist
                        closest_person_id = pid
                
                if closest_person_id is not None and min_dist < LUGGAGE_PROXIMITY_THRESHOLD:
                    lug_track['owner_id'] = closest_person_id # Assign new owner (Persistent ID)
                    owner_nearby = True

            if owner_nearby:
                # Reset Timer
                lug_track['abandoned_timer'] = 0
            else:
                # Owner away or unknown -> Increment Timer
                lug_track['abandoned_timer'] += 1

    def update(self, detections, frame_number):
        """
        Updates the tracker state with new detections.
        
        Args:
            detections (list): List of dicts [{'track_id': int, 'class': str, 'bbox': [x1, y1, x2, y2], 'centroid': [cx, cy]}]
            frame_number (int): Current frame number
        """
        self.frame_count = frame_number
        current_ids = set()

        for det in detections:
            tid = det['track_id']
            current_ids.add(tid)
            
            if tid not in self.tracks:
                self.tracks[tid] = {
                    'bbox': deque(maxlen=self.history_len),
                    'centroid': deque(maxlen=self.history_len),
                    'class': det['class'],
                    'last_seen': frame_number,
                    'is_abandoned_event_triggered': False
                }
            
            self.tracks[tid]['bbox'].append(det['bbox'])
            self.tracks[tid]['centroid'].append(det['centroid'])
            self.tracks[tid]['last_seen'] = frame_number

        # Optional: Clean up old tracks (not strictly required for this demo but good practice)
        # self._cleanup_old_tracks(frame_number)

    def get_track(self, track_id):
        return self.tracks.get(track_id)

    def get_all_tracks(self):
        return self.tracks

