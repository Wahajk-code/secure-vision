
import numpy as np
import cv2
try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

class PoseKeypointFilter:
    """
    A lightweight filter that runs a Pose Estimation model (YOLOv8-Pose) 
    on specific regions of interest (ROI) to detect high-velocity arm movements.
    """
    def __init__(self, model_name='yolov8m-pose.pt'):
        self.model = None
        if YOLO:
            # We assume the model will be downloaded automatically by Ultralytics
            # or exists in the cache. 'yolov8m-pose.pt' is the Medium version (better accuracy).
            try:
                self.model = YOLO(model_name).to('cuda')
            except Exception as e:
                print(f"[Warning] Could not load Pose Model to CUDA: {e}. Trying fallback 'yolov8n-pose.pt'")
                try:
                    self.model = YOLO('yolov8n-pose.pt')
                except:
                     print("[Error] Failed to load any Pose model.")
        
        # History of keypoints for velocity calculation
        # Key: track_id, Value: list of (wrists_xy, timestamp)
        self.keypoint_history = {} 
        self.HISTORY_SIZE = 10

    def get_arm_velocity_score(self, frame, track_id, bbox):
        """
        Runs pose estimation on the person within the bbox.
        Returns a score (0.0 to 1.0) representing arm activity/velocity.
        """
        if not self.model:
            return 0.0, np.zeros((17, 2))

        # 1. Crop ROI (with padding)
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = map(int, bbox)
        pad = 20
        x1, y1 = max(0, x1-pad), max(0, y1-pad)
        x2, y2 = min(w, x2+pad), min(h, y2+pad)
        
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return 0.0, np.zeros((17, 2))

        # 2. Preprocess: Resize ROI to expected input size (e.g. 320px height) to help small object detection
        input_h = 320
        scale_factor = input_h / roi.shape[0]
        input_w = int(roi.shape[1] * scale_factor)
        input_roi = cv2.resize(roi, (input_w, input_h))

        # 3. Run Inference on Resized ROI
        results = self.model(input_roi, verbose=False, device=0, conf=0.01) 
        
        if not results or not results[0].keypoints or results[0].keypoints.shape[1] == 0:
            return 0.0, np.zeros((17, 2))

        # 4. Extract Keypoints and Scale Back
        kpts = results[0].keypoints.xy.cpu().numpy()[0]
        
        # Scale keypoints back to original ROI size
        kpts[:, 0] /= scale_factor
        kpts[:, 1] /= scale_factor
        
        # Check confidence? (kpts has confidence?) kpts.conf
        
        left_wrist = kpts[9]
        right_wrist = kpts[10]
        
        # Estimate torso center
        valid_torso = [p for p in [kpts[5], kpts[6], kpts[11], kpts[12]] if p[0] > 0]
        roi_h = max(y2 - y1, 1) # Ensure roi_h is always defined
        
        if len(valid_torso) > 0 and (left_wrist[0] > 0 or right_wrist[0] > 0):
            torso = np.mean(valid_torso, axis=0)
            
            dists = []
            if left_wrist[0] > 0: dists.append(np.linalg.norm(left_wrist - torso))
            if right_wrist[0] > 0: dists.append(np.linalg.norm(right_wrist - torso))
            
            contact_dist = min(dists)
            contact_score = 1.0 if contact_dist < (roi_h * 0.15) else 0.0
        else:
            contact_score = 0.0
        
        # Current Positions
        current_pose = (left_wrist, right_wrist)
        
        # 4. Calculate Velocity against history
        velocity_score = 0.0
        
        if track_id in self.keypoint_history:
            prev_pose_list = self.keypoint_history[track_id]
            
            # Compare with average of last few frames to get robust movement
            # For simplicity, compare with immediate previous
            if prev_pose_list:
                prev_lw, prev_rw = prev_pose_list[-1]
                
                # Euclidean distance moved
                d_left = np.linalg.norm(left_wrist - prev_lw)
                d_right = np.linalg.norm(right_wrist - prev_rw)
                
                # Normalize by ROI height
                norm_factor = roi_h if roi_h > 0 else 1.0
                
                speed_l = d_left / norm_factor
                speed_r = d_right / norm_factor
                
                # Total speed score
                velocity_score = (speed_l + speed_r) * 100 # Scale up
                
        final_score = velocity_score + (contact_score * 50)
                
        # Update History
        if track_id not in self.keypoint_history:
            self.keypoint_history[track_id] = []
        self.keypoint_history[track_id].append(current_pose)
        if len(self.keypoint_history[track_id]) > self.HISTORY_SIZE:
             self.keypoint_history[track_id].pop(0)

        # Draw Debug Info on ROI (which is a view of Frame)
        self._draw_debug(roi, kpts, final_score)
             
        return final_score, kpts

    def _draw_debug(self, roi, kpts, velocity_score):
        """Draws full skeleton on the ROI."""
        pass
