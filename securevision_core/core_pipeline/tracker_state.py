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

    def assign_owners(self):
        """
        Associates luggage (backpack, handbag, suitcase) with the closest person.
        Updates 'owner_id' and 'abandoned_timer' for each luggage track.
        """
        from config import LUGGAGE_CLASSES, LUGGAGE_PROXIMITY_THRESHOLD

        persons = []
        luggage = []

        # Separate people and luggage
        for tid, track in self.tracks.items():
            # Check if track was updated recently (e.g. within last 5 frames) to be considered 'active'
            if self.frame_count - track['last_seen'] > 10:
                continue

            if track['class'] == 'person':
                persons.append((tid, track['centroid'][-1]))
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

            closest_person_id = None
            min_dist = float('inf')

            # Find closest person
            for pid, p_centroid in persons:
                dist = np.linalg.norm(lug_centroid - np.array(p_centroid))
                if dist < min_dist:
                    min_dist = dist
                    closest_person_id = pid
            
            # Check threshold
            if closest_person_id is not None and min_dist < LUGGAGE_PROXIMITY_THRESHOLD:
                # Owner Found - Reset Timer
                lug_track['owner_id'] = closest_person_id
                lug_track['abandoned_timer'] = 0
            else:
                # No Owner Nearby or Owner Left - Increment Timer
                # We assume assign_owners is called once per frame
                lug_track['abandoned_timer'] += 1
                # If timer exceeds threshold, we might keep the last owner_id or clear it?
                # Let's keep the last owner_id if it existed, so we know who left it.
                # lug_track['owner_id'] remains as is (last known owner) or None if never owned.

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
                    'last_seen': frame_number
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
