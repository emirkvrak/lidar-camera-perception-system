
from src.domain.base.transformable_model import TransformableModel


class WorldPointModel(TransformableModel):

    def __init__(self, x: float, y: float, z: float):
        super().__init__(x=x, y=y, z=z, yaw=0.0, pitch=0.0, roll=0.0)
