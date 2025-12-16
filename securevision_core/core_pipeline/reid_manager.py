import torch
import torch.nn as nn
from torchvision import models, transforms
from collections import deque
import numpy as np
from config import USE_CUDA

class ReIDManager:
    def __init__(self, use_cuda=USE_CUDA):
        self.device = torch.device('cuda' if use_cuda and torch.cuda.is_available() else 'cpu')
        print(f"[ReID] Initializing MobileNetV3 on {self.device}...")
        
        # Load Pretrained Model (MobileNetV3 Large)
        # We only need the backbone for features
        self.model = models.mobilenet_v3_large(pretrained=True)
        # Remove classification head to get embeddings (1280-dim vector)
        # The 'classifier' part usually processes the output of 'avgpool'.
        # We can just forward through the backbone or replace classifier with Identity.
        # Structure: features -> avgpool -> classifier
        self.model.classifier = nn.Identity()
        self.model.to(self.device).eval()
        
        # Store known identities
        # Format: { persistent_id: { 'embeddings': deque(maxlen=5), 'last_seen': frame_num } }
        self.known_identities = {}
        self.next_id = 1
        
        # Preprocessing
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        self.similarity_threshold = 0.5 # Cosine similarity threshold (0-1). Tune this.

    def extract_features(self, frame, bbox):
        """
        Extracts 1280-dim feature vector from the person crop.
        bbox: [x1, y1, x2, y2]
        """
        x1, y1, x2, y2 = map(int, bbox)
        
        # Clip bbox to frame dimensions
        h, w, _ = frame.shape
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)
        
        if x2 - x1 < 10 or y2 - y1 < 10:
            return None # Too small
            
        crop = frame[y1:y2, x1:x2]
        
        try:
            tensor = self.transform(crop).unsqueeze(0).to(self.device)
            with torch.no_grad():
                embedding = self.model(tensor)
                # Normalize embedding
                embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
                return embedding.cpu() # Keep on CPU for storage
        except Exception as e:
            print(f"[ReID] Extraction Failed: {e}")
            return None

    def find_match(self, embedding):
        """
        Compares embedding against known identities.
        Returns (matched_id, score) or (None, 0.0)
        """
        best_score = -1.0
        best_id = None
        
        if embedding is None:
            return None, 0.0

        for pid, data in self.known_identities.items():
            # Check against recent embeddings of this person
            # We can average them or max-score them. Max score is often more robust for quick retrieval.
            # Compare against the mean of stored embeddings for stability?
            # Let's compare against ALL stored embeddings and take max.
            
            stored_embeddings = torch.cat(list(data['embeddings'])) # Shape [N, 1280]
            # embedding is [1, 1280]
            
            # Compute cosine similarity
            sims = torch.nn.functional.cosine_similarity(embedding, stored_embeddings)
            max_sim = sims.max().item()
            
            if max_sim > best_score:
                best_score = max_sim
                best_id = pid
                
        if best_score > self.similarity_threshold:
            return best_id, best_score
        
        return None, best_score

    def update_identity(self, persistent_id, embedding, frame_num):
        """
        Updates the feature bank for an ID.
        """
        if embedding is None:
            return

        if persistent_id not in self.known_identities:
            self.known_identities[persistent_id] = {
                'embeddings': deque(maxlen=5), # Keep last 5 features
                'last_seen': frame_num
            }
        
        self.known_identities[persistent_id]['embeddings'].append(embedding)
        self.known_identities[persistent_id]['last_seen'] = frame_num

    def register_new_identity(self, embedding, frame_num):
        """
        Creates a new persistent ID.
        """
        pid = int(self.next_id)
        self.next_id += 1
        self.update_identity(pid, embedding, frame_num)
        return pid
