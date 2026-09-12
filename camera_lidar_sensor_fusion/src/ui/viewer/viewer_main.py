import tkinter as tk

from src.ui.viewer.viewer_canvas import ViewerCanvas
from src.ui.viewer.viewer_panel import ViewerPanel


class ViewerMain:
    def __init__(
        self,
        camera_projection,
        lidar_projection,
        camera_service,
        lidar_service,
        config_manager,
        on_close=None,
    ):
        # Projection sistemleri
        self.camera_ps = camera_projection
        self.lidar_ps = lidar_projection

        # Servisler
        self.camera_service = camera_service
        self.lidar_service = lidar_service

        # Yapılandırma
        self.config = config_manager
        self.on_close = on_close

        # Ana pencere
        self.root = tk.Tk()
        self.root.title("Mesan")
        self.root.state("zoomed")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

        # Görüntü alanı
        self.canvas = ViewerCanvas(
            master=self.root,
            projection_system=self.camera_ps,
            camera_service=self.camera_service,
            lidar_service=self.lidar_service,
            config_manager=self.config,
        )
        self.canvas.widget.grid(row=0, column=0, sticky="nsew")

        # Panel alanı
        self.panel_container = tk.Frame(self.root)
        self.panel_container.grid(row=1, column=0, pady=6, sticky="ew")
        self.panel_container.grid_columnconfigure(0, weight=1)

        # Ayar paneli
        self.panel = ViewerPanel(
            master=self.panel_container,
            projection_system=self.camera_ps,
            viewer_canvas=self.canvas,
            config_manager=self.config,
            lidar_service=self.lidar_service,
            lidar_projection=self.lidar_ps,
        )
        self.panel.frame.pack(side="top", pady=4, anchor="center")

    def _on_close(self):
        self.canvas.stop_loop()
        if self.on_close:
            self.on_close()
        self.root.destroy()

    def start(self):
        self.canvas.start_loop()
        self.root.mainloop()
