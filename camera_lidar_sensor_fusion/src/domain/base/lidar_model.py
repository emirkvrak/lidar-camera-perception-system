from src.domain.base.transformable_model import TransformableModel

class LidarModel(TransformableModel):
    
    def __init__(self, x=0.0, y=0.0, z=0.0, yaw=0.0, pitch=0.0, roll=0.0):
        super().__init__(x, y, z, yaw, pitch, roll)

