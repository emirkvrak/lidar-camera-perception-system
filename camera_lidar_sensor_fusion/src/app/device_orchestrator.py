
from typing import List

from src.core.projection.camera_projection_system import CameraProjectionSystem
from src.core.projection.lidar_projection_system import LidarProjectionSystem

from src.infrastructure.camera.camera_services import CameraService
from src.infrastructure.lidar.lidar_service import LidarService

from src.domain.base.camera_model import CameraModel
from src.domain.base.lidar_model import LidarModel


class DeviceOrchestrator:
    def __init__(self, ctx):
        self.ctx = ctx
        self.camera_models: List[CameraModel] = []
        self.lidar_models: List[LidarModel] = []

    def init_cameras(self) -> None:
        print("[DeviceOrchestrator] Kameralar başlatılıyor")

        camera_service = CameraService()
        self.ctx.services_registry.register("camera", camera_service)
        self.ctx.services.camera = camera_service

        camera_service.start_all()

        if not camera_service.cameras:
            print("[DeviceOrchestrator] UYARI: Fiziksel kamera bulunamadı (devam ediliyor)")
        else:
            print(f"[DeviceOrchestrator] {len(camera_service.cameras)} kamera aktif")

    def build_camera_models(self) -> None:
        print("[DeviceOrchestrator] Kamera modelleri oluşturuluyor")

        cfg_cameras = self.ctx.config.cameras
        if not cfg_cameras:
            raise RuntimeError("Kamera konfigürasyonu boş")

        self.camera_models.clear()

        for cam_cfg in cfg_cameras:
            cam = CameraModel()

            extr = cam_cfg["extrinsic"]
            intr = cam_cfg["intrinsic"]

            cam.set_transform(
                extr["x"], extr["y"], extr["z"],
                extr["yaw"], extr["pitch"], extr["roll"]
            )

            cam.set_intrinsics(
                intr["fx"], intr["fy"], intr["cx"], intr["cy"],
                intr.get("k1", 0.0),
                intr.get("k2", 0.0),
                intr.get("k3", 0.0),
                intr.get("p1", 0.0),
                intr.get("p2", 0.0),
            )

            self.camera_models.append(cam)

        print(f"[DeviceOrchestrator] {len(self.camera_models)} kamera modeli hazır")

    def init_lidars(self) -> None:

        print("[DeviceOrchestrator] Lidar servisi oluşturuluyor")

        lidar_service = LidarService()
        self.ctx.services_registry.register("lidar", lidar_service)
        self.ctx.services.lidar = lidar_service

    def build_lidar_models(self) -> None:
        print("[DeviceOrchestrator] Lidar modelleri oluşturuluyor")

        cfg_lidars = self.ctx.config.lidars
        if not cfg_lidars:
            raise RuntimeError("Lidar konfigürasyonu boş")

        self.lidar_models.clear()

        for lidar_cfg in cfg_lidars:
            lidar = LidarModel()

            extr = lidar_cfg["extrinsic"]
            lidar.set_transform(
                extr["x"], extr["y"], extr["z"],
                extr["yaw"], extr["pitch"], extr["roll"]
            )

            self.lidar_models.append(lidar)

        print(f"[DeviceOrchestrator] {len(self.lidar_models)} lidar modeli hazır")


    def init_projection(self) -> None:

        print("[DeviceOrchestrator] Projection sistemleri kuruluyor")

        self.ctx.systems.camera_projection = CameraProjectionSystem(self.camera_models)

        self.ctx.systems.lidar_projection = LidarProjectionSystem(
            self.lidar_models
        )

        lidar_service = self.ctx.services.lidar
        if lidar_service is None:
            print("[DeviceOrchestrator] UYARI: LidarService yok (init_lidars çağrılmadı)")
            return

        lidar_service.set_projection(self.ctx.systems.lidar_projection)
        lidar_service.start_all()

        if not lidar_service.lidars:
            print("[DeviceOrchestrator] UYARI: Fiziksel lidar bulunamadı (devam ediliyor)")
        else:
            print(f"[DeviceOrchestrator] {len(lidar_service.lidars)} lidar aktif")

    def init_all(self) -> None:

        self.init_cameras()
        self.build_camera_models()

        self.build_lidar_models()
        self.init_lidars()

        self.init_projection()
