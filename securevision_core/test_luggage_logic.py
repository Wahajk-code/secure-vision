import sys
import os
import unittest
import numpy as np
from collections import deque

# Adjust path to import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_pipeline.tracker_state import TrackerState
from config import LUGGAGE_PROXIMITY_THRESHOLD

class TestLuggageLogic(unittest.TestCase):
    def setUp(self):
        self.tracker = TrackerState()
        self.frame_num = 0

    def step(self):
        self.frame_num += 1
        return self.frame_num

    def test_owner_assignment_and_persistence(self):
        # 1. Setup: Person (ID 1) and Backpack (ID 99) close together
        p1_pos = [100, 100]
        bag_pos = [105, 105] # Within threshold (usually 200px)

        detections = [
            {'track_id': 1, 'class': 'person', 'bbox': [0,0,0,0], 'centroid': p1_pos},
            {'track_id': 99, 'class': 'backpack', 'bbox': [0,0,0,0], 'centroid': bag_pos}
        ]
        
        self.tracker.update(detections, self.step())
        self.tracker.assign_owners()

        bag_track = self.tracker.get_track(99)
        self.assertEqual(bag_track['owner_id'], 1, "Owner should be assigned to Person 1")
        self.assertEqual(bag_track['abandoned_timer'], 0, "Timer should be 0")

        # 2. Person leaves (moves far away)
        p1_pos = [1000, 1000] # Far away
        detections = [
            {'track_id': 1, 'class': 'person', 'bbox': [0,0,0,0], 'centroid': p1_pos},
            {'track_id': 99, 'class': 'backpack', 'bbox': [0,0,0,0], 'centroid': bag_pos}
        ]
        self.tracker.update(detections, self.step())
        self.tracker.assign_owners()

        self.assertEqual(bag_track['owner_id'], 1, "Owner ID should persist even if away")
        self.assertGreater(bag_track['abandoned_timer'], 0, "Timer should increment when owner leaves")
        timer_after_leave = bag_track['abandoned_timer']

        # 3. Random Person (ID 2) walks by close to bag
        p2_pos = [105, 105] # Close to bag
        detections = [
            {'track_id': 1, 'class': 'person', 'bbox': [0,0,0,0], 'centroid': p1_pos}, # Owner still far
            {'track_id': 2, 'class': 'person', 'bbox': [0,0,0,0], 'centroid': p2_pos}, # Stranger close
            {'track_id': 99, 'class': 'backpack', 'bbox': [0,0,0,0], 'centroid': bag_pos}
        ]
        self.tracker.update(detections, self.step())
        self.tracker.assign_owners()

        self.assertEqual(bag_track['owner_id'], 1, "Owner should NOT change to stranger")
        self.assertGreater(bag_track['abandoned_timer'], timer_after_leave, "Timer should CONTINUE incrementing even with stranger nearby")

        # 4. Owner returns
        p1_pos = [105, 105] # Owner comes back
        detections = [
            {'track_id': 1, 'class': 'person', 'bbox': [0,0,0,0], 'centroid': p1_pos},
            {'track_id': 99, 'class': 'backpack', 'bbox': [0,0,0,0], 'centroid': bag_pos}
        ]
        self.tracker.update(detections, self.step())
        self.tracker.assign_owners()

        self.assertEqual(bag_track['owner_id'], 1, "Owner should still be 1")
        self.assertEqual(bag_track['abandoned_timer'], 0, "Timer should RESET when OWNER returns")

    def test_alert_flag_initialization(self):
        bag_pos = [100, 100]
        detections = [
            {'track_id': 50, 'class': 'suitcase', 'bbox': [0,0,0,0], 'centroid': bag_pos}
        ]
        self.tracker.update(detections, self.step())
        
        bag_track = self.tracker.get_track(50)
        self.assertIn('is_abandoned_event_triggered', bag_track, "Flag should be initialized")
        self.assertFalse(bag_track['is_abandoned_event_triggered'], "Flag should be False initially")

if __name__ == '__main__':
    unittest.main()
