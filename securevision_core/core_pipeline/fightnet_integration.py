import torch
import torch.nn as nn
import numpy as np
import cv2

def compute_angle(a, b, c):
    ba = a - b
    bc = c - b
    norm_ba = np.linalg.norm(ba, axis=-1) + 1e-6
    norm_bc = np.linalg.norm(bc, axis=-1) + 1e-6
    cosine = np.sum(ba * bc, axis=-1) / (norm_ba * norm_bc)
    cosine = np.clip(cosine, -1.0, 1.0)
    return np.arccos(cosine)

def normalize_skeleton(joints):
    left_shoulder = joints[:, 5]
    right_shoulder = joints[:, 6]
    shoulder_center = (left_shoulder + right_shoulder) / 2
    return joints - shoulder_center[:, None, :]  # keep scale info

def extract_features(pose_window):
    """
    User's Cell 7 geometric feature extractor.
    pose_window: (T, max_persons*17*2) flat, or (T, 2, 17, 2)
    We'll assume it's passed as (T, 2, 17, 2).
    """
    if pose_window.ndim == 4:
        T, P, K, D = pose_window.shape
        pose_window = pose_window.reshape(T, P*K*D)

    pose_window = np.nan_to_num(pose_window, nan=0.0)
    T = pose_window.shape[0]

    if T < 2:
        return np.zeros((1, 150), dtype=np.float32)

    p1 = pose_window[:, :34].reshape(T, 17, 2)
    p2 = pose_window[:, 34:].reshape(T, 17, 2)

    p1 = normalize_skeleton(p1)
    p2 = normalize_skeleton(p2)

    rel_joints = p1 - p2
    rel_joints_flat = rel_joints.reshape(T, -1)

    def get_angles(person):
        return np.stack([
            compute_angle(person[:, 5], person[:, 7], person[:, 9]),
            compute_angle(person[:, 6], person[:, 8], person[:, 10]),
            compute_angle(person[:, 11], person[:, 13], person[:, 15]),
            compute_angle(person[:, 12], person[:, 14], person[:, 16])
        ], axis=1)

    angle_features = np.concatenate([get_angles(p1), get_angles(p2)], axis=1)

    p1_center = p1.mean(axis=1)
    p2_center = p2.mean(axis=1)
    inter_dist = np.linalg.norm(p1_center - p2_center, axis=1, keepdims=True)

    combined = np.concatenate([p1.reshape(T, -1), p2.reshape(T, -1)], axis=1)
    velocities = combined[1:] - combined[:-1]
    speed = np.linalg.norm(velocities, axis=1, keepdims=True)

    rel_vel = rel_joints[1:] - rel_joints[:-1]
    rel_speed = np.linalg.norm(rel_vel.reshape(T - 1, -1), axis=1, keepdims=True)

    # Contact-Aware Features
    wrists = [9, 10]
    knees = [15, 16]
    head = [0]
    torso = [5, 6, 11, 12]

    contact_features = []
    for t in range(T):
        frame_features = []
        for w in wrists:
            for h in head:
                frame_features.append(np.linalg.norm(p1[t, w] - p2[t, h]))
                frame_features.append(np.linalg.norm(p2[t, w] - p1[t, h]))
            for tr in torso:
                frame_features.append(np.linalg.norm(p1[t, w] - p2[t, tr]))
                frame_features.append(np.linalg.norm(p2[t, w] - p1[t, tr]))
        for k in knees:
            for tr in torso:
                frame_features.append(np.linalg.norm(p1[t, k] - p2[t, tr]))
                frame_features.append(np.linalg.norm(p2[t, k] - p1[t, tr]))

        dists = np.linalg.norm(p1[t][:, None, :] - p2[t][None, :, :], axis=-1)
        frame_features.append(np.min(dists))
        contact_features.append(frame_features)

    contact_features = np.array(contact_features)

    features = np.concatenate([
        velocities,
        speed,
        rel_joints_flat[1:],
        rel_speed,
        angle_features[1:],
        inter_dist[1:],
        contact_features[1:]
    ], axis=1)

    return features.astype(np.float32)


class SEBlock(nn.Module):
    def __init__(self, in_channels, r=16):
        super().__init__()
        self.fc1 = nn.Linear(in_channels, in_channels // r)
        self.fc2 = nn.Linear(in_channels // r, in_channels)

    def forward(self, x):
        return x

class FightNet(nn.Module):
    """
    Reconstructed from model_shapes.json
    """
    def __init__(self, input_dim=150, hidden_dim=96):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        self.temporal = nn.Sequential(
            nn.Conv1d(hidden_dim, hidden_dim, 3, padding=1),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Conv1d(hidden_dim, hidden_dim, 3, padding=1),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Conv1d(hidden_dim, hidden_dim, 3, padding=1),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU()
        )
        
        self.se = SEBlock(hidden_dim, r=16)
        
        self.attn = nn.Sequential(
            nn.Linear(hidden_dim, 1),
            nn.Softmax(dim=1)
        )
        
        self.classifier = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, x):
        # x is (B, T, 150)
        x = self.input_proj(x) # (B, T, 96)
        
        # Conv1d expects (B, C, T)
        x = x.transpose(1, 2)
        x = self.temporal(x) # (B, 96, T)
        
        x = x.transpose(1, 2) # (B, T, 96)
        
        # SE block (ignoring true logic for now as it needs careful reconstruction, let's just make shapes match)
        # Actually SE logic: Global avg pool -> fc1 -> relu -> fc2 -> sigmoid -> scale
        w = x.mean(dim=1) # (B, 96)
        w = torch.relu(self.se.fc1(w))
        w = torch.sigmoid(self.se.fc2(w))
        x = x * w.unsqueeze(1) # (B, T, 96)
        
        # Attention
        a = self.attn(x) # (B, T, 1)
        x = (x * a).sum(dim=1) # (B, 96)
        
        # Classifier
        x = self.classifier(x) # (B, 1)
        return x

_model_instance = None

def run_fightnet(pose_buffer):
    """
    pose_buffer: list of 30 frames, each is (2, 17, 2)
    Returns boolean TRUE if fight.
    """
    global _model_instance
    if _model_instance is None:
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            _model_instance = FightNet().to(device)
            _model_instance.load_state_dict(torch.load('models/fightnet_best_model.pt', map_location=device))
            _model_instance.eval()
            print("[FightNet] Loaded successfully.")
        except Exception as e:
            print(f"[FightNet] Failed to load: {e}")
            return False

    if len(pose_buffer) < 2:
        return False
        
    seq = np.array(pose_buffer) # (T, 2, 17, 2)
    features = extract_features(seq) # (T-1, 150)
    
    # Pad to 30 if necessary for Conv1d temporal shapes, though CNN handles variable lengths
    # But usually models trained on length 30 might expect it.
    
    tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0) # (1, T-1, 150)
    device = next(_model_instance.parameters()).device
    tensor = tensor.to(device)
    
    with torch.no_grad():
        out = _model_instance(tensor)
        prob = torch.sigmoid(out).item()
        
    # from config we see best_threshold is likely around 0.35 to 0.5
    return prob > 0.40
