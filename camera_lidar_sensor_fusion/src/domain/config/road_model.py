from dataclasses import dataclass

@dataclass
class RoadModel:
    name: str
    visible: bool
    road_type: str           # geliş | gidiş | ikisi
    lane_width: float
    incoming_count: int
    outgoing_count: int
    color: str = "#000000"

    @staticmethod
    def from_dict(data: dict) -> "RoadModel":
        return RoadModel(
            name=data.get("name", "Unnamed Road"),
            visible=data.get("visible", True),
            road_type=data.get("type", "incoming"),
            lane_width=data.get("lane_width", 3.75),
            incoming_count=data.get("incoming", {}).get("count", 0),
            outgoing_count=data.get("outgoing", {}).get("count", 0),
            color=data.get("color", "#FFFFFF"),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "visible": self.visible,
            "type": self.road_type,
            "lane_width": self.lane_width,
            "color": self.color,
            "incoming": {
                "count": self.incoming_count
            },
            "outgoing": {
                "count": self.outgoing_count
            },
        }
