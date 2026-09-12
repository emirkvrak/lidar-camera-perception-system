"""Açık LiDAR algoritmalarını kurumsal olmayan sentetik veriyle çalıştırır."""

import numpy as np

from public_algorithms.detection import build_detections, cluster_points
from public_algorithms.preprocessing import (
    filter_points_by_road_and_range,
    voxel_filter_weighted,
)
from public_algorithms.tracking import MultiObjectTracker


def make_frame(frame_index: int, rng: np.random.Generator):
    """İki hareketli nokta kümesi ve az miktarda gürültü oluşturur."""

    first = np.column_stack(
        [
            rng.normal(-2.0, 0.35, 80),
            rng.normal(0.6, 0.12, 80),
            rng.normal(25.0 + frame_index * 0.8, 0.45, 80),
        ]
    )
    second = np.column_stack(
        [
            rng.normal(2.0, 0.35, 80),
            rng.normal(0.7, 0.12, 80),
            rng.normal(42.0 + frame_index * 0.5, 0.45, 80),
        ]
    )
    noise = np.column_stack(
        [
            rng.uniform(-6.0, 6.0, 12),
            rng.uniform(-1.0, 2.0, 12),
            rng.uniform(15.0, 70.0, 12),
        ]
    )

    points = np.vstack([first, second, noise]).astype(np.float32)
    photons = rng.integers(1, 20, len(points), dtype=np.uint32)
    directions = rng.integers(0, 4, len(points), dtype=np.uint32)
    return points, photons, directions


def main():
    rng = np.random.default_rng(7)
    tracker = MultiObjectTracker()
    lane_intervals = [(-6.0, 0.0), (0.0, 6.0)]

    for frame_index in range(6):
        points, photons, directions = make_frame(frame_index, rng)

        mask = filter_points_by_road_and_range(
            points,
            lane_intervals=lane_intervals,
            shrink=0.25,
            min_height=0.1,
            min_forward=15.0,
            max_forward=70.0,
        )
        points = points[mask]
        photons = photons[mask]
        directions = directions[mask]

        points, photons, directions = voxel_filter_weighted(
            points,
            photons,
            directions,
            voxel_size=0.25,
        )

        labels, clusters, sizes, noise_count = cluster_points(
            points,
            eps=1.2,
            min_samples=5,
        )
        detections = build_detections(
            points,
            photons,
            timestamp=frame_index * 0.1,
            labels=labels,
            unique_clusters=clusters,
            min_points_per_cluster=4,
        )
        entities = tracker.update(detections, dt=0.1)

        print(
            f"frame={frame_index} "
            f"points={len(points)} "
            f"clusters={len(sizes)} "
            f"noise={noise_count} "
            f"detections={len(detections)} "
            f"confirmed_tracks={len(entities)}"
        )


if __name__ == "__main__":
    main()
