import tkinter as tk
from tkinter import ttk


class ViewerPanel:
    def __init__(self, master, projection_system, viewer_canvas, config_manager, lidar_service=None, lidar_projection=None):
        self.master = master
        self.ps = projection_system          # Kamera projeksiyonu
        self.canvas = viewer_canvas
        self.config = config_manager

        self.lidar_service = lidar_service
        self.canvas.lidar_service = lidar_service
        self.lidar_ps = lidar_projection

        # Arayüz değişkenleri
        self.active_camera_var = tk.StringVar()
        self.active_camera_index = tk.IntVar(value=0)

        self.frame = tk.Frame(self.master)
        self.frame.pack(fill="x", padx=10, pady=6)

        self.show_roads_var = tk.BooleanVar(value=True)
        self.show_markers_var = tk.BooleanVar(value=True)
        self.show_lidar_var = tk.BooleanVar(value=True)

        self.road_type_var = tk.StringVar()
        self.lane_width_var = tk.DoubleVar()
        self.incoming_count_var = tk.IntVar()
        self.outgoing_count_var = tk.IntVar()

        self.entries = {}       # Kamera girişleri
        self.lidar_entries = {} # Lidar girişleri

        self.incoming_entry = None
        self.outgoing_entry = None

        self._load_from_config()
        self._build_ui()

        # Arayüz oluşturulduktan sonra
        self._load_lidar_params()
        self._on_road_type_change()
        self._load_camera_params()

    def _load_from_config(self):
        # Şerit ayarları
        if getattr(self.config, "roads", None):
            if self.config.roads:
                road = self.config.roads[0]
                self.road_type_var.set(getattr(road, "road_type", "incoming"))
                self.lane_width_var.set(getattr(road, "lane_width", 3.75))
                self.incoming_count_var.set(getattr(road, "incoming_count", 0))
                self.outgoing_count_var.set(getattr(road, "outgoing_count", 0))
                self.show_roads_var.set(bool(getattr(road, "visible", True)))

        # Marker ayarları
        if getattr(self.config, "markers", None):
            if self.config.markers:
                self.show_markers_var.set(bool(getattr(self.config.markers[0], "visible", True)))

        # LiDAR ayarları
        if getattr(self.config, "lidars", None) and len(self.config.lidars) > 0:
            lidar_cfg = self.config.lidars[0]
            self.show_lidar_var.set(bool(lidar_cfg.get("visible", True)))
        else:
            self.show_lidar_var.set(True)

        # Görüntü üzerindeki çizim ayarları
        self.canvas.show_roads = bool(self.show_roads_var.get())
        self.canvas.show_markers = bool(self.show_markers_var.get())
        self.canvas.show_lidar = bool(self.show_lidar_var.get())

    def _apply_road_settings(self):
        if not getattr(self.config, "roads", None) or not self.config.roads:
            return

        road = self.config.roads[0]
        road.road_type = self.road_type_var.get()
        road.lane_width = float(self.lane_width_var.get())
        road.incoming_count = int(self.incoming_count_var.get())
        road.outgoing_count = int(self.outgoing_count_var.get())
        road.visible = bool(self.show_roads_var.get())

        self.canvas.show_roads = bool(self.show_roads_var.get())

        if hasattr(self.config, "save_roads"):
            self.config.save_roads()

    def _apply_marker_settings(self):
        visible = bool(self.show_markers_var.get())
        if getattr(self.config, "markers", None):
            for marker in self.config.markers:
                marker.visible = visible

        self.canvas.show_markers = visible

        if hasattr(self.config, "save_markers"):
            self.config.save_markers()

    def _apply_lidar_settings(self):
        visible = bool(self.show_lidar_var.get())
        self.canvas.show_lidar = visible

        def get_val(key: str) -> float:
            try:
                return float(self.lidar_entries[key].get())
            except Exception:
                return 0.0

        x = get_val("x"); y = get_val("y"); z = get_val("z")
        yaw = get_val("yaw"); pitch = get_val("pitch"); roll = get_val("roll")

        if not hasattr(self.config, "lidars") or self.config.lidars is None:
            self.config.lidars = []

        if len(self.config.lidars) == 0:
            self.config.lidars.append({"name": "Lidar1", "extrinsic": {}})

        lidar_cfg = self.config.lidars[0]
        lidar_cfg["visible"] = visible
        lidar_cfg.setdefault("extrinsic", {})

        ext = lidar_cfg["extrinsic"]
        ext["x"], ext["y"], ext["z"] = x, y, z
        ext["yaw"], ext["pitch"], ext["roll"] = yaw, pitch, roll

        # Değişiklikleri aktif LiDAR modeline de uygula.
        lidar_models = getattr(self.lidar_ps, "lidar_models", []) if self.lidar_ps else []
        if lidar_models:
            lidar_models[0].set_transform(x, y, z, yaw, pitch, roll)


        self.config.save_lidar()

    def _apply_camera_settings(self):
        cam, idx = self._get_active_camera()
        if cam is None:
            return

        def f(n: str) -> float:
            return float(self.entries[n].get())

        cam.set_intrinsics(
            f("fx"), f("fy"), f("cx"), f("cy"),
            f("k1"), f("k2"), f("k3"), f("p1"), f("p2")
        )
        cam.set_transform(
            f("x"), f("y"), f("z"),
            f("yaw"), f("pitch"), f("roll")
        )

        if getattr(self.config, "cameras", None) and idx < len(self.config.cameras):
            cfg_cam = self.config.cameras[idx]
            cfg_cam["extrinsic"].update({
                "x": cam.x, "y": cam.y, "z": cam.z,
                "yaw": cam.yaw, "pitch": cam.pitch, "roll": cam.roll
            })
            cfg_cam["intrinsic"].update({
                "fx": cam.fx, "fy": cam.fy, "cx": cam.cx, "cy": cam.cy,
                "k1": cam.k1, "k2": cam.k2, "k3": cam.k3, "p1": cam.p1, "p2": cam.p2
            })

        if hasattr(self.config, "save_cameras"):
            self.config.save_cameras()

    def _update_overlays(self):
        self._apply_road_settings()
        self._apply_marker_settings()
        self._apply_lidar_settings()

    def _get_active_camera(self):
        if self.ps is None or not hasattr(self.ps, "model_devices"):
            return None, 0

        devices = getattr(self.ps, "model_devices", None) or []
        if not devices:
            return None, 0

        idx = int(self.active_camera_index.get())
        idx = max(0, min(idx, len(devices) - 1))
        return devices[idx], idx

    def _load_camera_params(self):
        cam, _ = self._get_active_camera()
        if cam is None:
            return

        params = {
            "fx": cam.fx, "fy": cam.fy, "cx": cam.cx, "cy": cam.cy,
            "k1": cam.k1, "k2": cam.k2, "k3": cam.k3, "p1": cam.p1, "p2": cam.p2,
            "x": cam.x, "y": cam.y, "z": cam.z,
            "yaw": cam.yaw, "pitch": cam.pitch, "roll": cam.roll
        }
        for k, v in params.items():
            if k in self.entries:
                self.entries[k].delete(0, tk.END)
                self.entries[k].insert(0, str(v))

    def _on_road_type_change(self, event=None):
        rt = self.road_type_var.get()
        if not self.incoming_entry or not self.outgoing_entry:
            return

        if rt == "incoming":
            self.outgoing_count_var.set(0)
            self.incoming_entry.config(state="normal")
            self.outgoing_entry.config(state="disabled")
        elif rt == "outgoing":
            self.incoming_count_var.set(0)
            self.incoming_entry.config(state="disabled")
            self.outgoing_entry.config(state="normal")
        else:
            self.incoming_entry.config(state="normal")
            self.outgoing_entry.config(state="normal")

    def _load_lidar_params(self):
        if not hasattr(self.config, "lidars") or not self.config.lidars:
            return

        lidar_cfg = self.config.lidars[0]
        extr = lidar_cfg.get("extrinsic", {}) or {}

        defaults = {"x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0, "pitch": 0.0, "roll": 0.0}
        for key, default in defaults.items():
            val = extr.get(key, default)
            if key in self.lidar_entries:
                self.lidar_entries[key].delete(0, tk.END)
                self.lidar_entries[key].insert(0, str(val))

    def _build_ui(self):
        top = tk.LabelFrame(self.frame, text="Görünürlük & Kayıt")
        top.pack(fill="x", pady=5)

        tk.Checkbutton(top, text="Şeritleri Göster", variable=self.show_roads_var, command=self._update_overlays)\
            .pack(side="left", padx=10)
        tk.Checkbutton(top, text="Dubaları Göster", variable=self.show_markers_var, command=self._update_overlays)\
            .pack(side="left", padx=10)
        tk.Checkbutton(top, text="Lidar Göster", variable=self.show_lidar_var, command=self._update_overlays)\
            .pack(side="left", padx=10)

        bottom = tk.Frame(self.frame)
        bottom.pack(fill="x", pady=6)

        left = tk.LabelFrame(bottom, text="Kamera Ayarları")
        left.pack(side="left", fill="both", expand=True, padx=5)

        right_container = tk.Frame(bottom)
        right_container.pack(side="right", fill="both", expand=True, padx=5)

        right_top = tk.LabelFrame(right_container, text="Şerit Ayarları")
        right_top.pack(side="top", fill="x", pady=(0, 5))

        right_bottom = tk.LabelFrame(right_container, text="Lidar Ayarları")
        right_bottom.pack(side="top", fill="x")

        # Kamera ayarları
        tk.Label(left, text="Aktif Kamera").pack(pady=4)

        if self.ps is None or not hasattr(self.ps, "model_devices") or not self.ps.model_devices:
            tk.Label(left, text="Kamera modeli yok (projection hazır değil)").pack(pady=6)
            cam_names = []
        else:
            cam_names = [f"cam{i+1}" for i in range(len(self.ps.model_devices))]

        if cam_names:
            self.active_camera_var.set(cam_names[0])

        cam_selector = ttk.Combobox(
            left, values=cam_names, state="readonly", width=8, textvariable=self.active_camera_var
        )
        cam_selector.pack(pady=4)

        def on_cam_selected(_e):
            if not cam_names:
                return
            idx = cam_names.index(self.active_camera_var.get())
            self.active_camera_index.set(idx)
            if hasattr(self.canvas, "set_active_camera"):
                self.canvas.set_active_camera(idx)
            self._load_camera_params()

        cam_selector.bind("<<ComboboxSelected>>", on_cam_selected)

        def add_cam_entry(parent, row, col, name):
            tk.Label(parent, text=name).grid(row=row, column=col, sticky="w")
            e = tk.Entry(parent, width=6)
            e.grid(row=row, column=col + 1, padx=2, pady=2)
            self.entries[name] = e

        intrinsic = tk.LabelFrame(left, text="Kamera iç parametreleri")
        intrinsic.pack(side="left", fill="both", expand=True, padx=2)
        extrinsic = tk.LabelFrame(left, text="Kamera dış parametreleri")
        extrinsic.pack(side="right", fill="both", expand=True, padx=2)

        add_cam_entry(intrinsic, 0, 0, "fx"); add_cam_entry(intrinsic, 0, 2, "fy")
        add_cam_entry(intrinsic, 1, 0, "cx"); add_cam_entry(intrinsic, 1, 2, "cy")
        add_cam_entry(intrinsic, 2, 0, "k1"); add_cam_entry(intrinsic, 2, 2, "k2")
        add_cam_entry(intrinsic, 3, 0, "k3"); add_cam_entry(intrinsic, 3, 2, "p1")
        add_cam_entry(intrinsic, 4, 0, "p2")

        add_cam_entry(extrinsic, 0, 0, "x"); add_cam_entry(extrinsic, 0, 2, "y")
        add_cam_entry(extrinsic, 1, 0, "z")
        add_cam_entry(extrinsic, 2, 0, "yaw"); add_cam_entry(extrinsic, 2, 2, "pitch")
        add_cam_entry(extrinsic, 3, 0, "roll")

        tk.Button(left, text="KAYDET (Kamera)", bg="#44AA44", fg="white", command=self._apply_camera_settings)\
            .pack(pady=5)

        # Şerit ayarları
        tk.Label(right_top, text="Tip").grid(row=0, column=0, sticky="w", padx=4)
        road_type_cb = ttk.Combobox(
            right_top, textvariable=self.road_type_var,
            values=["incoming", "outgoing", "both"], state="readonly", width=8
        )
        road_type_cb.grid(row=0, column=1, padx=4)
        road_type_cb.bind("<<ComboboxSelected>>", self._on_road_type_change)

        tk.Label(right_top, text="Genişlik").grid(row=0, column=2, sticky="w", padx=4)
        tk.Entry(right_top, textvariable=self.lane_width_var, width=6).grid(row=0, column=3, padx=4)

        tk.Label(right_top, text="Geliş").grid(row=1, column=0, sticky="w", padx=4)
        self.incoming_entry = tk.Entry(right_top, textvariable=self.incoming_count_var, width=6)
        self.incoming_entry.grid(row=1, column=1, padx=4, pady=2)

        tk.Label(right_top, text="Gidiş").grid(row=1, column=2, sticky="w", padx=4)
        self.outgoing_entry = tk.Entry(right_top, textvariable=self.outgoing_count_var, width=6)
        self.outgoing_entry.grid(row=1, column=3, padx=4, pady=2)

        tk.Button(right_top, text="KAYDET (Şerit)", bg="#4477AA", fg="white", command=self._apply_road_settings)\
            .grid(row=2, column=0, columnspan=4, pady=4)

        # LiDAR ayarları
        def add_lidar_entry(parent, row, col, name):
            tk.Label(parent, text=name).grid(row=row, column=col, sticky="w", padx=4)
            e = tk.Entry(parent, width=6)
            e.grid(row=row, column=col + 1, padx=4, pady=2)
            self.lidar_entries[name] = e

        add_lidar_entry(right_bottom, 0, 0, "x"); add_lidar_entry(right_bottom, 0, 2, "y")
        add_lidar_entry(right_bottom, 0, 4, "z")
        add_lidar_entry(right_bottom, 1, 0, "yaw"); add_lidar_entry(right_bottom, 1, 2, "pitch")
        add_lidar_entry(right_bottom, 1, 4, "roll")

        tk.Button(right_bottom, text="KAYDET (Lidar)", bg="#AA4444", fg="white", command=self._apply_lidar_settings)\
            .grid(row=2, column=0, columnspan=6, pady=4)
