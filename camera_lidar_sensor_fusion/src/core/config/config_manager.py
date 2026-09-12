from src.domain.config.marker_model import MarkerModel
from src.domain.config.road_model import RoadModel
from src.infrastructure.config.config_repository import ConfigRepository


class ConfigManager:

    def __init__(
        self,
        road_repo: ConfigRepository,
        marker_repo: ConfigRepository,
        camera_repo: ConfigRepository,
        lidar_repo: ConfigRepository,  
    ):
        self._road_repo = road_repo
        self._marker_repo = marker_repo
        self._camera_repo = camera_repo
        self._lidar_repo = lidar_repo  

        self.roads: list[RoadModel] = []
        self.markers: list[MarkerModel] = []
        self.cameras: list[dict] = []
        self.lidars: list[dict] = []   

    def load_all_json(self) -> None:
        
        # Yapılandırmalar dosyalardan okunuyor.
        road_data = self._road_repo.load_from_json().get("roads", [])
        marker_data = self._marker_repo.load_from_json().get("markers", [])
        camera_data = self._camera_repo.load_from_json().get("cameras", [])
        lidar_data = self._lidar_repo.load_from_json().get("lidars", []) 

        # Veriler model nesnelerine veya sözlüklere dönüştürülüyor.
        self.roads = [RoadModel.from_dict(rd) for rd in road_data]
        self.markers = [MarkerModel.from_dict(mk) for mk in marker_data]
        self.cameras = camera_data
        self.lidars = lidar_data  

        print("[ConfigManager] Konfigürasyonlar yüklendi (domain)")

    def save_roads(self) -> None:
        self._road_repo.save_write_json({
            "roads": [r.to_dict() for r in self.roads]
        })

    def save_markers(self) -> None:
        self._marker_repo.save_write_json({
            "markers": [m.to_dict() for m in self.markers]
        })

    def save_cameras(self) -> None:
        self._camera_repo.save_write_json({
            "cameras": self.cameras
        })

    def save_lidar(self) -> None:  
        self._lidar_repo.save_write_json({
            "lidars": self.lidars
        })
