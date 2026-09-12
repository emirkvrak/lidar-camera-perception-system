import numpy as np


class TransformableModel:
    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        yaw: float = 0.0,
        pitch: float = 0.0,
        roll: float = 0.0,
    ):
        # -----------------------------
        # Position (world)
        # -----------------------------
        self.position = np.array([x, y, z], dtype=float)

        # -----------------------------
        # Orientation (degrees)
        # -----------------------------
        self._yaw = float(yaw)
        self._pitch = float(pitch)
        self._roll = float(roll)

    # ==================================================
    # Position properties (UI & domain uyumlu)
    # ==================================================
    @property
    def x(self):
        return float(self.position[0])

    @x.setter
    def x(self, v):
        self.position[0] = float(v)

    @property
    def y(self):
        return float(self.position[1])

    @y.setter
    def y(self, v):
        self.position[1] = float(v)

    @property
    def z(self):
        return float(self.position[2])

    @z.setter
    def z(self, v):
        self.position[2] = float(v)

    # ==================================================
    # Rotation properties (UI & domain uyumlu)
    # ==================================================
    @property
    def yaw(self):
        return self._yaw

    @yaw.setter
    def yaw(self, v):
        self._yaw = float(v)

    @property
    def pitch(self):
        return self._pitch

    @pitch.setter
    def pitch(self, v):
        self._pitch = float(v)

    @property
    def roll(self):
        return self._roll

    @roll.setter
    def roll(self, v):
        self._roll = float(v)

    # ==================================================
    # Transform helpers
    # ==================================================
    def set_position(self, x, y, z):
        self.position[:] = (float(x), float(y), float(z))

    def get_position(self):
        return self.position.copy()

    def set_rotation(self, yaw, pitch, roll):
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

    def set_transform(self, x, y, z, yaw, pitch, roll):
        self.set_position(x, y, z)
        self.set_rotation(yaw, pitch, roll)

    # ==================================================
    # World → Camera rotation & translation
    # (kamera +X yönüne bakıyor varsayımı)
    # ==================================================
    def get_world_transform(self):
        yaw   = np.radians(self.yaw + 90.0)
        pitch = np.radians(self.pitch)
        roll  = -np.radians(self.roll)

        cy, sy = np.cos(yaw), np.sin(yaw)
        cp, sp = np.cos(pitch), np.sin(pitch)
        cr, sr = np.cos(roll), np.sin(roll)

        # YAW (Y ekseni)
        Ryaw = np.array([
            [ cy, 0.0,  sy],
            [ 0.0, 1.0, 0.0],
            [-sy, 0.0,  cy],
        ])

        # PITCH (X ekseni)
        Rpitch = np.array([
            [1.0, 0.0,  0.0],
            [0.0,  cp, -sp],
            [0.0,  sp,  cp],
        ])

        # ROLL (Z ekseni)
        Rroll = np.array([
            [ cr, -sr, 0.0],
            [ sr,  cr, 0.0],
            [0.0,  0.0, 1.0],
        ])

        # Kamera → Dünya rotasyonu
        R = Rroll @ Rpitch @ Ryaw

        # Translation
        t = self.position.reshape(3, 1)

        return R, t
