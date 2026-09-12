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

        self.widget = tk.Label(
            master,
            bg="black",
            highlightthickness=1,
            highlightbackground="white",
            highlightcolor="white",
        )
        self.widget.grid(row=0, column=0, sticky="nsew")
        self.widget.bind("<Configure>", self._on_resize)
        self.widget.bind("<Button-1>", self._on_click)

        self.tk_image = None
        self.width = 800
        self.height = 600

        # Kameralar için ortak görüntü boyutu kullanılıyor.
        self.virtual_frame_size = self._get_virtual_frame_size()

        # Görüntü üzerine çizilecek öğeler
        self.show_roads = True
        self.show_markers = True
        self.show_lidar = True

        self.active_camera_index = 0
        self.focus_index = None

        self._last_frame_count = 0
        self._last_img_width = 1
        self._after_id = None

    def set_active_camera(self, index: int):
        self.active_camera_index = int(index)

    def _on_resize(self, event):
        self.width = max(event.width, 1)
        self.height = max(event.height, 1)

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

    def start_loop(self):
        if self._after_id is None:
            self._update_frame()

    def stop_loop(self):
        if self._after_id is not None:
            try:
                self.master.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _get_virtual_frame_size(self):
        camera_configs = getattr(self.config, "cameras", [])
        image_sizes = [
            camera.get("image_size", {})
            for camera in camera_configs
            if camera.get("image_size")
        ]

        if image_sizes:
            width = int(image_sizes[0].get("width", 2700))
            height = int(image_sizes[0].get("height", 1000))
            return max(1, width), max(1, height)

        return 2700, 1000

    def _create_virtual_frame(self):
        """Fiziksel kamera yoksa siyah görüntü oluşturur."""
        width, height = self.virtual_frame_size
        return np.zeros((height, width, 3), dtype=np.uint8)

    def _draw_overlays(self, frame, cam_key: str):

        # Şeritler
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
                        segment = []

                        for z in z_vals:
                            proj = self.ps.project_xyz(lane_x, 0.0, z)
                            uv = safe_get_uv(proj.get(cam_key))
                            if uv:
                                segment.append(uv)
                            else:
                                if len(segment) >= 2:
                                    draw_polyline(frame, segment, bgr, 4)
                                segment = []

                        if len(segment) >= 2:
                            draw_polyline(frame, segment, bgr, 4)

        # Markerlar
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

        # LiDAR noktaları
        if self.show_lidar and self.lidar_service:
            # Beklenen çıktı: List[np.ndarray] -> [x, y, z]
            points = self.lidar_service.get_tracked_points()

            for p in points:
                proj = self.ps.project_xyz(p[0], p[1], p[2])
                uv = safe_get_uv(proj.get(cam_key))

                if uv:
                    draw_point(frame, uv, (0, 255, 255), 8)

        return frame

    def _update_frame(self):
        frames = []

        physical_cameras = self.camera_service.cameras
        model_cameras = getattr(self.ps, "model_devices", [])
        camera_count = max(len(physical_cameras), len(model_cameras), 1)

        for idx in range(camera_count):
            cam = physical_cameras[idx] if idx < len(physical_cameras) else None
            is_virtual = cam is None or cam.frame is None or cam.frame.size == 0

            if is_virtual:
                f = self._create_virtual_frame()
            else:
                f = cam.frame.copy()

            cam_key = f"cam{idx + 1}"

            f = self._draw_overlays(f, cam_key)

            if is_virtual or idx == self.active_camera_index:
                cv2.rectangle(
                    f,
                    (5, 5),
                    (f.shape[1] - 5, f.shape[0] - 5),
                    (255, 255, 255),
                    2
                )

            frames.append(f)

        self._last_frame_count = len(frames)

        if not frames:
            final = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.rectangle(
                final,
                (1, 1),
                (final.shape[1] - 2, final.shape[0] - 2),
                (255, 255, 255),
                1,
            )
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

        # Görüntü oranını koruyarak ekrana sığdır.
        scale = min(self.width / final.shape[1], self.height / final.shape[0])
        resized_width = max(1, int(final.shape[1] * scale))
        resized_height = max(1, int(final.shape[0] * scale))
        resized_final = cv2.resize(final, (resized_width, resized_height))

        fitted = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        offset_x = (self.width - resized_width) // 2
        offset_y = (self.height - resized_height) // 2
        fitted[
            offset_y:offset_y + resized_height,
            offset_x:offset_x + resized_width,
        ] = resized_final
        final = fitted

        self._last_img_width = final.shape[1]

        img = ImageTk.PhotoImage(
            Image.fromarray(cv2.cvtColor(final, cv2.COLOR_BGR2RGB))
        )
        self.tk_image = img
        self.widget.config(image=img)

        self._after_id = self.master.after(15, self._update_frame)
