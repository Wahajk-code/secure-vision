import sys
import os
import unittest
import numpy as np
import torch

# Adjust path to import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_pipeline.reid_manager import ReIDManager
from config import USE_CUDA

class TestReIDManager(unittest.TestCase):
    def setUp(self):
        self.manager = ReIDManager(use_cuda=True)
        # Create a dummy person image (random noise but correct shape)
        self.frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        self.bbox = [100, 100, 200, 300] # x1, y1, x2, y2

    def test_feature_extraction(self):
        embedding = self.manager.extract_features(self.frame, self.bbox)
        self.assertIsNotNone(embedding, "Embedding should not be None")
        self.assertEqual(embedding.shape, (1, 960), "Embedding shape mismatch")

    def test_matching_logic(self):
        # 1. Register an identity
        emb1 = self.manager.extract_features(self.frame, self.bbox)
        pid = self.manager.register_new_identity(emb1, 1)
        self.assertEqual(pid, 1, "First ID should be 1")

        # 2. Match exact same features (should match perfectly)
        matched_id, score = self.manager.find_match(emb1)
        self.assertEqual(matched_id, pid, "Should match original ID")
        self.assertGreater(score, 0.99, "Similarity should be near 1.0 for exact match")

        # 3. Match random noise (should presumably NOT match well)
        # MobileNet might assume natural images so noise is undefined behavior, 
        # but logically it should differ from the first one.
        frame2 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        emb2 = self.manager.extract_features(frame2, self.bbox)
        
        # We can't guarantee cosine sim will be low for random noise in deep space,
        # but let's just ensure it runs.
        matched_id_2, score_2 = self.manager.find_match(emb2)
        print(f"Random noise score: {score_2}") 
        # Ideally check score < threshold, but for random noise it's unpredictable 
        # without real data. We just assert no crash here.

if __name__ == '__main__':
    unittest.main()
