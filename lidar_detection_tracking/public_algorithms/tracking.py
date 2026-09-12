"""Projeye katkı olarak geliştirilen çoklu nesne takip algoritmaları."""

from collections import deque
from typing import Any, Dict, List

import numpy as np
from scipy.optimize import linear_sum_assignment


MIN_FORWARD = 15.0
MAX_FORWARD = 70.0


class Track:
    def __init__(self, track_id, detection, timestamp):
        self.id = track_id
        self.speed_lp = 0.0
        self.speed_buffer = deque(maxlen=7)

        # state = [forward, lateral, v_forward, v_lateral]
        self.prev_forward = float(detection["meas_pos"][0])
        self.state = np.zeros((4, 1), dtype=np.float32)
        self.state[0:2] = detection["meas_pos"].reshape(2, 1)

        self.P = np.diag([1.0, 1.0, 25.0, 25.0]).astype(np.float32)
        self.H = np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0]],
            dtype=np.float32,
        )
        self.R = np.diag([0.3, 0.3]).astype(np.float32)

        self.position3d = detection["position3d"]
        self.position_std = detection["position_std"]
        self.bbox2d = detection["bbox2d"]
        self.bbox3d = detection["bbox3d"]
        self.last_timestamp = float(timestamp)

        self.hits = 1
        self.misses = 0
        self.is_confirmed = False

    def predict(self, dt):
        if dt <= 0:
            return

        F = np.array(
            [
                [1, 0, dt, 0],
                [0, 1, 0, dt],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ],
            dtype=np.float32,
        )
        Q = np.diag([0.02, 0.02, 1.5, 1.5]).astype(np.float32)

        self.state = F @ self.state
        self.P = F @ self.P @ F.T + Q

    def update(self, detection, dt):
        measurement = detection["meas_pos"].reshape(2, 1)
        innovation = measurement - self.H @ self.state
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.state = self.state + K @ innovation
        self.P = (np.eye(4) - K @ self.H) @ self.P

        forward = float(measurement[0, 0])
        if dt > 0:
            measured_velocity = (forward - self.prev_forward) / dt

            if len(self.speed_buffer) >= 5:
                mean_ms = np.mean(self.speed_buffer) / 3.6
                max_delta_ms = 6.0 / 3.6
                measured_velocity = np.clip(
                    measured_velocity,
                    mean_ms - max_delta_ms,
                    mean_ms + max_delta_ms,
                )

            beta = 0.2
            self.speed_lp = (
                (1 - beta) * self.speed_lp + beta * measured_velocity
            )
            self.speed_buffer.append(self.speed_lp * 3.6)

        self.prev_forward = forward
        self.position3d = detection["position3d"]
        self.position_std = detection["position_std"]
        self.bbox2d = detection["bbox2d"]
        self.bbox3d = detection["bbox3d"]
        self.hits += 1
        self.misses = 0
        self.last_timestamp = float(detection["timestamp"])

    def get_speed_3d(self):
        return np.array(
            [0.0, 0.0, float(self.state[2, 0])],
            dtype=np.float32,
        )

    def get_speed_std_3d(self):
        if len(self.speed_buffer) < 5:
            return np.zeros(3, dtype=np.float32)

        std_ms = float(np.std(self.speed_buffer)) / 3.6
        return np.array([0.0, 0.0, std_ms], dtype=np.float32)


class MultiObjectTracker:
    def __init__(self):
        self.tracks = []
        self.next_id = 1
        self.dist_threshold = 6.0
        self.max_misses = 10
        self.min_hits_to_confirm = 3

    def update(self, detections, dt):
        for track in self.tracks:
            track.predict(dt)

        num_old_tracks = len(self.tracks)
        num_detections = len(detections)

        if num_detections == 0:
            alive = []
            for track in self.tracks:
                track.misses += 1
                if track.hits >= self.min_hits_to_confirm:
                    track.is_confirmed = True
                if track.misses <= self.max_misses:
                    alive.append(track)
            self.tracks = alive
            return self._output()

        cost = np.full(
            (num_old_tracks, num_detections),
            1e6,
            dtype=np.float32,
        )

        for track_index, track in enumerate(self.tracks):
            predicted = track.state[0:2].flatten()
            for detection_index, detection in enumerate(detections):
                distance = np.linalg.norm(
                    predicted - detection["meas_pos"]
                )
                if distance < self.dist_threshold:
                    cost[track_index, detection_index] = distance

        row_idx, col_idx = linear_sum_assignment(cost)
        assigned_tracks = set()
        assigned_detections = set()

        for row, column in zip(row_idx, col_idx):
            if cost[row, column] >= self.dist_threshold:
                continue
            self.tracks[row].update(detections[column], dt)
            assigned_tracks.add(row)
            assigned_detections.add(column)

        for detection_index, detection in enumerate(detections):
            if detection_index not in assigned_detections:
                self.tracks.append(
                    Track(self.next_id, detection, detection["timestamp"])
                )
                self.next_id += 1

        alive = []
        for index, track in enumerate(self.tracks[:num_old_tracks]):
            if index not in assigned_tracks:
                track.misses += 1
            else:
                track.misses = 0

            if track.hits >= self.min_hits_to_confirm:
                track.is_confirmed = True
                forward = float(track.position3d[2])
                if forward < MIN_FORWARD + 1 or forward > MAX_FORWARD - 1:
                    continue

            if not track.is_confirmed and track.misses > 2:
                continue
            if track.is_confirmed and track.misses > self.max_misses:
                continue
            alive.append(track)

        alive.extend(self.tracks[num_old_tracks:])
        self.tracks = alive
        return self._output()

    def _output(self) -> List[Dict[str, Any]]:
        entities = []
        for track in self.tracks:
            if not track.is_confirmed:
                continue

            entities.append(
                {
                    "identifier": track.id,
                    "position": track.position3d,
                    "position_std": track.position_std,
                    "speed": track.get_speed_3d(),
                    "speed_std": track.get_speed_std_3d(),
                    "is_valid": track.is_confirmed,
                    "boundaries": track.bbox3d,
                }
            )
        return entities
