from dataclasses import dataclass

from src.domain.base.world_point_model import WorldPointModel

@dataclass
class MarkerModel:

    name: str
    visible: bool
    position: WorldPointModel
    size: dict
    color: str = "#FFFFFF"
    

    def from_dict(data:dict) -> "MarkerModel":
        return MarkerModel(
            name=data.get("name", "Unnamed Marker"),
            visible=data.get("visible", True),
            position = WorldPointModel(
                data.get("position", {}).get("x",0.0),
                data.get("position", {}).get("y",0.0),
                data.get("position", {}).get("z",0.0),
            ),
            size={
                "width": data.get("size", {}).get("width", 0.3),
                "height": data.get("size", {}).get("height", 0.75),
            },
            color=data.get("color", "#FFFFFF"),
        )
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "visible": self.visible,
            "position": {
                "x": self.position.x,
                "y": self.position.y,
                "z": self.position.z,
            },
            "size": self.size,
            "color": self.color,
        }