import json
import os
from typing import Dict, List


DEFAULT_CAMERAS = [
    {"id": "cam_01", "name": "Camera 1", "sector": "Sector A", "area": "Area A - Main Entrance", "is_active": True},
    {"id": "cam_02", "name": "Camera 2", "sector": "Sector B", "area": "Area B - Lobby", "is_active": True},
    {"id": "cam_03", "name": "Camera 3", "sector": "Sector C", "area": "Area C - Corridor", "is_active": True},
    {"id": "cam_04", "name": "Camera 4", "sector": "Sector D", "area": "Area D - Parking", "is_active": True},
]


class CameraRegistry:
    def __init__(self, path=None):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.path = path or os.path.join(base_dir, "camera_config.json")

    def list_cameras(self) -> List[Dict]:
        if not os.path.exists(self.path):
            self.save_cameras(DEFAULT_CAMERAS)
            return list(DEFAULT_CAMERAS)

        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
            cameras = data.get("cameras", data if isinstance(data, list) else [])
            if not cameras:
                return list(DEFAULT_CAMERAS)
            return [self._merge_defaults(camera, index) for index, camera in enumerate(cameras[:4])]
        except Exception:
            return list(DEFAULT_CAMERAS)

    def save_cameras(self, cameras: List[Dict]) -> List[Dict]:
        normalized = [self._merge_defaults(camera, index) for index, camera in enumerate(cameras[:4])]
        while len(normalized) < 4:
            normalized.append(dict(DEFAULT_CAMERAS[len(normalized)]))

        with open(self.path, "w", encoding="utf-8") as file:
            json.dump({"cameras": normalized}, file, indent=2)
        return normalized

    def get_camera(self, camera_id="cam_01") -> Dict:
        for camera in self.list_cameras():
            if camera["id"] == camera_id:
                return camera
        return dict(DEFAULT_CAMERAS[0])

    @staticmethod
    def _merge_defaults(camera: Dict, index: int) -> Dict:
        default = dict(DEFAULT_CAMERAS[index])
        default.update({
            "id": str(camera.get("id") or default["id"]),
            "name": str(camera.get("name") or default["name"]),
            "sector": str(camera.get("sector") or default["sector"]),
            "area": str(camera.get("area") or default["area"]),
            "is_active": bool(camera.get("is_active", default["is_active"])),
        })
        return default
