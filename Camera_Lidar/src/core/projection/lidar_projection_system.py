import numpy as np
import numpy.typing as npt
from typing import List, Optional, Tuple


class LidarProjectionSystem:

    def __init__(self, lidar_models, roads=None):
        self.lidar_models = lidar_models
        self.roads = roads or []

        self.min_height = -0.3
        self.max_height = 3.0

        self.min_forward = 0.0
        self.max_forward = 120.0


        self.lane_filter_on = False
        self.voxel_on = False

        self.debug = True
        self._debug_printed = False

    def project_and_filter(
        self,
        cartesian: np.ndarray,
        photon_count: np.ndarray,
        direction_id=None,
    ):
        if cartesian is None or cartesian.size == 0:
            return (
                np.zeros((0, 3), dtype=np.float32),
                photon_count,
                direction_id,
            )

        cartesian = cartesian.astype(np.float32, copy=False)

        cartesian = cartesian[:, [0, 2, 1]]

        lidar = self.lidar_models[0]             
        R, t = lidar.get_world_transform()        

        cartesian = (R @ cartesian.T).T + t.reshape(1, 3)

        x = cartesian[:, 0]
        y = cartesian[:, 1]
        z = cartesian[:, 2]

        mask_h = (y >= -2.0) & (y <= 3.0)
        mask_f = (z >= 0.0) & (z <= 120.0)
        mask = mask_h & mask_f

        cartesian = cartesian[mask]
        photon_count = photon_count[mask]
        if direction_id is not None:
            direction_id = direction_id[mask]

        return cartesian, photon_count, direction_id


    def _filter_by_lane(self, pts: np.ndarray) -> np.ndarray:
        return pts

    def _voxelize(self, pts: np.ndarray, photon_count: np.ndarray):
        return pts, photon_count
