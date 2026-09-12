import cv2
from typing import Tuple, List

def draw_point(frame, uv: Tuple[int, int], color: Tuple[int, int, int], radius: int = 8):
    cv2.circle(frame, uv, radius + 2, (0, 0, 0), -1)
    cv2.circle(frame, uv, radius, color, -1)

def draw_line(frame, uv1: Tuple[int, int], uv2: Tuple[int, int],
              color: Tuple[int, int, int], thickness: int = 2):
    cv2.line(frame, uv1, uv2, color, thickness, cv2.LINE_AA)

def draw_polyline(frame, points: List[Tuple[int, int]],
                  color: Tuple[int, int, int], thickness: int = 2):
    if len(points) < 2:
        return
    for i in range(len(points) - 1):
        draw_line(frame, points[i], points[i + 1], color, thickness)
