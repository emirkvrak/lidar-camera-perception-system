# src/ui/viewer/viewer_canvas.py

import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
import cv2

from src.domain.base.world_point_model import WorldPointModel
from src.ui.drawing.paint import draw_point, draw_polyline
from src.ui.drawing.safe_uv import safe_get_uv


class ViewerCanvas:
    def __init__(self, master, projection_system, camera_service, lidar_service, config_manager):
        self.master = master
        self.ps = projection_system
        self.camera_service = camera_service
        self.lidar_service = lidar_service
        self.config = config_manager

        self.widget = tk.Label(master, bg="black")
        self.widget.grid(row=0, column=0, sticky="nsew")
        self.widget.bind("<Configure>", self._on_resize)
        self.widget.bind("<Button-1>", self._on_click)

        self.tk_image = None
        self.width = 800
        self.height = 600

        # Overlay flags
        self.show_roads = True
        self.show_markers = True
        self.show_lidar = True

        self.active_camera_index = 0
        self.focus_index = None

        self._last_frame_count = 0
        self._last_img_width = 1
        self._last_img_height = 1

    # --------------------------------------------------
    def set_active_camera(self, index: int):
        self.active_camera_index = int(index)

    # --------------------------------------------------
    def _on_resize(self, event):
        self.width = max(event.width, 1)
        self.height = max(event.height, 1)

    # --------------------------------------------------
    def _on_click(self, event):
        if self.focus_index is not None:
            self.focus_index = None
            return

        if self._last_frame_count <= 0:
            return

        rel_x = event.x / max(self._last_img_width, 1)
        idx = int(rel_x * self._last_frame_count)

        if 0 <= idx < self._last_frame_count:
            self.focus_index = idx

    # --------------------------------------------------
    def start_loop(self):
        self._update_frame()

    # --------------------------------------------------
    def _draw_overlays(self, frame, cam_key: str):

        # ========== ROADS ==========
        if self.show_roads:
            for road in self.config.roads:
                if not road.visible:
                    continue

                hex_color = road.color.lstrip("#")
                bgr = tuple(int(hex_color[i:i + 2], 16) for i in (4, 2, 0))

                z_vals = [75.0, 0.0, -75.0]

                for side in ("incoming", "outgoing"):
                    if road.road_type not in (side, "both"):
                        continue

                    offset = 0.0 if side == "incoming" else road.incoming_count * road.lane_width
                    count = road.incoming_count if side == "incoming" else road.outgoing_count

                    for i in range(count + 1):
                        lane_x = offset + i * road.lane_width
                        pts = []

                        for z in z_vals:
                            proj = self.ps.project_xyz(lane_x, 0.0, z)
                            uv = safe_get_uv(proj.get(cam_key))
                            if uv:
                                pts.append(uv)

                        if len(pts) >= 2:
                            draw_polyline(frame, pts, bgr, 4)

        # ========== MARKERS ==========
        if self.show_markers:
            for m in self.config.markers:
                if not m.visible:
                    continue

                hex_color = m.color.lstrip("#")
                bgr = tuple(int(hex_color[i:i + 2], 16) for i in (4, 2, 0))

                bottom = m.position
                h = m.size.get("height", 0.75)
                top = WorldPointModel(bottom.x, bottom.y + h, bottom.z)

                pb = self.ps.project(bottom).get(cam_key)
                pt = self.ps.project(top).get(cam_key)

                uvb = safe_get_uv(pb)
                uvt = safe_get_uv(pt)

                if uvb:
                    draw_point(frame, uvb, bgr, 10)
                if uvb and uvt:
                    draw_polyline(frame, [uvb, uvt], bgr, 4)

        # ========== LIDAR (TRACKED CENTROIDS ONLY) ==========
        if self.show_lidar and self.lidar_service:
            # Beklenen çıktı: List[np.ndarray] -> [x, y, z]
            points = self.lidar_service.get_tracked_points()

            for p in points:
                proj = self.ps.project_xyz(p[0], p[1], p[2])
                uv = safe_get_uv(proj.get(cam_key))

                if uv:
                    draw_point(frame, uv, (0, 255, 255), 8)

        return frame

    # --------------------------------------------------
    def _update_frame(self):
        frames = []

        for idx, cam in enumerate(self.camera_service.cameras):
            if cam.frame is None or cam.frame.size == 0:
                continue

            f = cam.frame.copy()
            cam_key = f"cam{idx + 1}"

            f = self._draw_overlays(f, cam_key)

            if idx == self.active_camera_index:
                cv2.rectangle(
                    f,
                    (5, 5),
                    (f.shape[1] - 5, f.shape[0] - 5),
                    (0, 255, 0),
                    4
                )

            frames.append(f)

        self._last_frame_count = len(frames)

        if not frames:
            final = np.zeros((480, 640, 3), dtype=np.uint8)
        elif self.focus_index is not None:
            final = frames[self.focus_index]
        elif len(frames) == 1:
            final = frames[0]
        else:
            h = min(f.shape[0] for f in frames)
            resized = [
                cv2.resize(f, (int(f.shape[1] * h / f.shape[0]), h))
                for f in frames
            ]
            final = cv2.hconcat(resized)

        final = cv2.resize(final, (self.width, self.height))
        self._last_img_width = final.shape[1]
        self._last_img_height = final.shape[0]

        img = ImageTk.PhotoImage(
            Image.fromarray(cv2.cvtColor(final, cv2.COLOR_BGR2RGB))
        )
        self.tk_image = img
        self.widget.config(image=img)

        self.master.after(15, self._update_frame)
