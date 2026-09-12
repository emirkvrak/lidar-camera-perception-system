from typing import Optional, Tuple
from collections import defaultdict
import numpy as np


def voxel_filter_weighted(
    points: np.ndarray,
    photon_count: np.ndarray,
    direction_id: Optional[np.ndarray] = None,
    voxel_size: float = 0.25
) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:

    if points is None or points.size == 0:
        return (
            np.zeros((0, 3), dtype=np.float32),
            np.zeros((0,), dtype=np.float32),
            None if direction_id is None else np.zeros((0,), dtype=np.int32),
        )

    points = np.asarray(points, dtype=np.float32)
    photon_count = np.asarray(photon_count, dtype=np.float32)
    if direction_id is not None:
        direction_id = np.asarray(direction_id, dtype=np.int32)

    voxel_coords = np.floor(points / voxel_size).astype(np.int32)

    voxel_dict = defaultdict(list)
    for i, v in enumerate(voxel_coords):
        voxel_dict[(v[0], v[1], v[2])].append(i)

    filtered_points = []
    filtered_photons = []
    filtered_dirs = [] if direction_id is not None else None

    for idx_list in voxel_dict.values():
        pts = points[idx_list]                       # (K,3)
        phs = photon_count[idx_list].astype(np.float64)

        ph_sum = float(phs.sum())

        # Weighted centroid
        if ph_sum > 0:
            w = phs / ph_sum
            mean_point = (pts * w[:, None]).sum(axis=0)
        else:
            mean_point = pts.mean(axis=0)

        # Photon aggregation: mean (istersen sum da yapabilirsin)
        mean_photon = float(phs.mean())

        filtered_points.append(mean_point)
        filtered_photons.append(mean_photon)

        # Direction: majority vote (kategorik varsayımı)
        if filtered_dirs is not None:
            dirs = direction_id[idx_list]
            values, counts = np.unique(dirs, return_counts=True)
            filtered_dirs.append(int(values[np.argmax(counts)]))

    new_points = np.asarray(filtered_points, dtype=np.float32)
    new_photons = np.asarray(filtered_photons, dtype=np.float32)
    new_dirs = np.asarray(filtered_dirs, dtype=np.int32) if filtered_dirs is not None else None

    return new_points, new_photons, new_dirs
