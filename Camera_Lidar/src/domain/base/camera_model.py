from src.domain.base.transformable_model import TransformableModel


class CameraModel(TransformableModel):

    def __init__(self, x=0, y=0, z=0, yaw=0, pitch=0, roll=0):
        super().__init__(x, y, z, yaw, pitch, roll)

        # -----------------------------
        # Intrinsic parameters
        # -----------------------------
        self.fx = 1000.0
        self.fy = 1000.0
        self.cx = 640.0
        self.cy = 360.0

        # -----------------------------
        # Distortion (Brown–Conrady)
        # -----------------------------
        self.k1 = 0.0
        self.k2 = 0.0
        self.k3 = 0.0
        self.p1 = 0.0
        self.p2 = 0.0

    def set_intrinsics(
        self,
        fx, fy, cx, cy,
        k1=0.0, k2=0.0, k3=0.0,
        p1=0.0, p2=0.0
    ):
        self.fx = float(fx)
        self.fy = float(fy)
        self.cx = float(cx)
        self.cy = float(cy)

        self.k1 = float(k1)
        self.k2 = float(k2)
        self.k3 = float(k3)
        self.p1 = float(p1)
        self.p2 = float(p2)
