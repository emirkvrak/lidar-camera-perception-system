# src/core/projection/camera_projection_system.py

from typing import Dict, List

from src.core.projection.projection_calculation import project_point_3d
from src.domain.base.transformable_model import TransformableModel


class CameraProjectionSystem:
    def __init__(self, model_cameras: List[TransformableModel]):
        # Projede her yerde bunu kullanıyorsun (ViewerPanel de model_devices bekliyor)
        self.model_devices = model_cameras

    def project(self, obj: TransformableModel) -> Dict[str, dict]:
        Pw = obj.get_position()
        results = {}

        for idx, cam in enumerate(self.model_devices):
            cam_key = f"cam{idx + 1}"
            u, v, visible = project_point_3d(cam, Pw)
            results[cam_key] = {"u": u, "v": v, "visible": visible}

        return results

    def project_xyz(self, x: float, y: float, z: float):
        from src.domain.base.world_point_model import WorldPointModel
        return self.project(WorldPointModel(x, y, z))
