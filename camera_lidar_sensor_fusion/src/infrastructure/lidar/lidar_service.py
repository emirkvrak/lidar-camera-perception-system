import asyncio
import threading
from typing import List, Optional
import os

import numpy as np

from src.infrastructure.lidar.lidar_driver import LidarDriver
from src.core.projection.lidar_projection_system import LidarProjectionSystem


class LidarService:
    def __init__(self):
        self.lidars: List[LidarDriver] = []
        self._tasks: List[asyncio.Future] = []

        self._lock = threading.Lock()
        self._world_points: np.ndarray | None = None

        # Asenkron döngü ayrı iş parçacığında çalışıyor.
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        # Ortak veri yolu: ana klasör/shared_data/lidar.data
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../../")
        )
        self.file_path = os.path.join(project_root, "shared_data", "lidar.data")

        # Veri oynatma ayarları
        self.fps: float = 10.0
        self.loop_forever: bool = True

        # Dışarıdan set edilecek
        self.lidar_projection: Optional[LidarProjectionSystem] = None

    def set_projection(self, lidar_projection: LidarProjectionSystem):
        self.lidar_projection = lidar_projection

    def update_world_points(self, points: np.ndarray):
        with self._lock:
            self._world_points = points.copy()

    def get_tracked_points(self) -> np.ndarray:
        with self._lock:
            if self._world_points is None:
                return np.zeros((0, 3), dtype=np.float32)
            return self._world_points

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def start(self):
        self.start_all()

    def start_all(self):
        if self.lidar_projection is None:
            print("[LidarService] HATA: lidar_projection set edilmemiş")
            return

        if not os.path.exists(self.file_path):
            print("[LidarService] HATA: lidar.data bulunamadı →", self.file_path)
            return

        # Tekrar başlatılmasın
        if self.lidars:
            print("[LidarService] Zaten çalışıyor (tekrar start geçildi)")
            return

        lidar_count = LidarDriver.get_lidar_count()

        for idx in range(lidar_count):
            lidar = LidarDriver(
                device_index=idx,
                file_path=self.file_path,
                lidar_projection=self.lidar_projection,
                on_points=self.update_world_points,
                fps=self.fps,
                loop_forever=self.loop_forever,
                debug=True,
                debug_every_n=10,
            )

            future = asyncio.run_coroutine_threadsafe(lidar.run_async(), self._loop)

            self.lidars.append(lidar)
            self._tasks.append(future)

        print(f"[LidarService] {len(self.lidars)} lidar playback aktif")

    def stop(self):
        self.shutdown()

    def shutdown(self):
        for lidar in self.lidars:
            lidar.stop()

        for task in self._tasks:
            try:
                task.cancel()
            except Exception:
                pass

        # Görevler iptal sinyalini işleyip tamamen bitsin.
        # Döngüyü hemen durdurmak, kapanışta "Task was destroyed" uyarısına
        # neden olabiliyordu.
        for task in self._tasks:
            try:
                task.result(timeout=1.0)
            except Exception:
                pass

        self._tasks.clear()
        self.lidars.clear()

        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread.is_alive():
            self._thread.join(timeout=1)
