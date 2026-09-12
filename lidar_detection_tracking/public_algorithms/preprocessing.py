"""Projeye katkı olarak geliştirilen LiDAR nokta bulutu ön işleme işlemleri.

Fonksiyonlar genel NumPy dizileriyle çalışır; özel playback dosyasına veya
kurumsal uygulama koduna bağlı değildir.
"""

from collections import defaultdict
from typing import Optional, Sequence, Tuple

import numpy as np


def filter_points_by_road_and_range(
    points: np.ndarray,
    lane_intervals: Sequence[Tuple[float, float]],
    shrink: float = 0.5,
    min_height: float = 0.1,
    min_forward: float = 15.0,
    max_forward: float = 70.0,
) -> np.ndarray:
    """Kullanılabilir yol bölgesindeki noktaların maskesini döndürür.

    Noktalar proje içindeki ``[lateral, height, forward]`` düzenindedir.
    ``lane_intervals`` her kullanılabilir şeridin yanal başlangıç/bitişini içerir.
    """

    if points.size == 0:
        return np.zeros(0, dtype=bool)

    lane_mask = np.zeros(len(points), dtype=bool)
    for start, end in lane_intervals:
        usable_start = start + shrink
        usable_end = end - shrink
        lane_mask |= (
            (points[:, 0] >= usable_start)
            & (points[:, 0] <= usable_end)
        )

    height_mask = points[:, 1] >= min_height
    forward_mask = (
        (points[:, 2] >= min_forward)
        & (points[:, 2] <= max_forward)
    )
    return lane_mask & height_mask & forward_mask


def voxel_filter_weighted(
    points: np.ndarray,
    photon_count: np.ndarray,
    direction_id: Optional[np.ndarray] = None,
    voxel_size: float = 0.25,
):
    """Photon count ağırlıklı voxel ortalamalarıyla nokta yoğunluğunu azaltır."""

    if points.size == 0:
        return points, photon_count, direction_id

    voxel_coords = (points / voxel_size).astype(np.int32)
    voxel_dict = defaultdict(list)

    for i, voxel in enumerate(voxel_coords):
        voxel_dict[(voxel[0], voxel[1], voxel[2])].append(i)

    filtered_points = []
    filtered_photons = []
    filtered_dirs = [] if direction_id is not None else None

    for idx_list in voxel_dict.values():
        pts = points[idx_list]
        phs = photon_count[idx_list].astype(np.float64)

        weight_sum = phs.sum()
        if weight_sum <= 0:
            mean_point = pts.mean(axis=0)
            mean_photon = 0.0
            if direction_id is not None:
                mean_dir = np.round(direction_id[idx_list].mean())
        else:
            weights = phs / weight_sum
            mean_point = (pts * weights[:, None]).sum(axis=0)
            mean_photon = weight_sum / len(idx_list)

            if direction_id is not None:
                dirs = direction_id[idx_list].astype(np.float64)
                mean_dir = np.round((dirs * weights).sum())

        filtered_points.append(mean_point)
        filtered_photons.append(mean_photon)
        if filtered_dirs is not None:
            filtered_dirs.append(mean_dir)

    new_points = np.array(filtered_points, dtype=np.float32)
    new_photons = np.array(filtered_photons, dtype=np.float32)
    new_dirs = (
        np.array(filtered_dirs, dtype=np.int32)
        if filtered_dirs is not None
        else direction_id
    )
    return new_points, new_photons, new_dirs
