"""Genel LiDAR noktaları için kümelendirme ve nesne özelliği çıkarımı."""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import DBSCAN


def cluster_points(
    points: np.ndarray,
    eps: float = 0.6,
    min_samples: int = 10,
) -> Tuple[np.ndarray, np.ndarray, Dict[int, int], int]:
    """Noktaları DBSCAN ile kümelendirir; gürültü ve küme boyutlarını döndürür."""

    if points.size == 0:
        return (
            np.array([], dtype=int),
            np.array([], dtype=int),
            {},
            0,
        )

    labels = DBSCAN(eps=eps, min_samples=min_samples).fit(points).labels_
    noise_count = int(np.sum(labels == -1))
    unique_clusters = np.array(
        [cluster for cluster in np.unique(labels) if cluster != -1]
    )

    cluster_sizes = {
        int(cluster): int(np.sum(labels == cluster))
        for cluster in unique_clusters
    }
    return labels, unique_clusters, cluster_sizes, noise_count


def build_detections(
    cartesian: np.ndarray,
    photon_count: np.ndarray,
    timestamp: float,
    labels: Optional[np.ndarray],
    unique_clusters: Optional[List[int]],
    min_points_per_cluster: int = 4,
) -> List[Dict[str, Any]]:
    """DBSCAN kümelerini takip sisteminin kullanacağı ölçümlere dönüştürür."""

    if labels is None or unique_clusters is None:
        return []

    detections: List[Dict[str, Any]] = []
    for cluster_id in unique_clusters:
        points = cartesian[labels == cluster_id]
        photons = photon_count[labels == cluster_id]

        if points.shape[0] < min_points_per_cluster:
            continue

        lateral_mean = points[:, 0].mean()
        height_mean = points[:, 1].mean()

        # A percentile is more stable than the furthest single point.
        forward_tip = np.percentile(points[:, 2], 5)

        position3d = np.array(
            [lateral_mean, height_mean, forward_tip],
            dtype=np.float32,
        )
        position_std = points.std(axis=0).astype(np.float32)
        measurement = np.array(
            [forward_tip, lateral_mean],
            dtype=np.float32,
        )

        min_xyz = points.min(axis=0)
        max_xyz = points.max(axis=0)

        detections.append(
            {
                "meas_pos": measurement,
                "position3d": position3d,
                "position_std": position_std,
                "bbox2d": np.array(
                    [min_xyz[2], min_xyz[0], max_xyz[2], max_xyz[0]],
                    dtype=np.float32,
                ),
                "bbox3d": np.stack([min_xyz, max_xyz]),
                "timestamp": timestamp,
                "photon_count": photons,
            }
        )

    return detections
