from dataclasses import dataclass, field

from src.core.lifecycle.services_registry import ServicesRegestry
from src.core.config.config_manager import ConfigManager
from src.infrastructure.config.config_repository import ConfigRepository
from src.infrastructure.config.default_json import (
    DEFAULT_CAMERAS_JSON, DEFAULT_MARKERS_JSON, DEFAULT_ROADS_JSON, DEFAULT_LIDARS_JSON
)


@dataclass
class Services:
    camera = None
    lidar = None 

@dataclass
class Systems:
    pass

@dataclass
class AppContext:
    services: Services = field(default_factory=Services)
    systems: Systems = field(default_factory=Systems)

    services_registry: ServicesRegestry = field(default_factory=ServicesRegestry)

    def __post_init__(self):
        print("[AppContext] Uygulama Bağlamı Oluşturuldu jsonlar oluşturuldu")

        road_repo = ConfigRepository("config/roads.json", DEFAULT_ROADS_JSON)
        marker_repo = ConfigRepository("config/markers.json", DEFAULT_MARKERS_JSON)
        camera_repo = ConfigRepository("config/cameras.json", DEFAULT_CAMERAS_JSON)
        lidar_repo = ConfigRepository("config/lidars.json", DEFAULT_LIDARS_JSON)

        self.config = ConfigManager(
            road_repo=road_repo,
            marker_repo=marker_repo,
            camera_repo=camera_repo,
            lidar_repo=lidar_repo  
        )
