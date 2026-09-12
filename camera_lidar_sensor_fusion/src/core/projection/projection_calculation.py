import numpy as np

from src.domain.base.transformable_model import TransformableModel


def project_point_3d(cam: TransformableModel, Pw):

    # 1) Dünya noktası
    Pw = np.asarray(Pw, dtype=float).reshape(3, 1)

    # 2) Dünya koordinatından kamera koordinatına geçiş
    R, t = cam.get_world_transform()
    Pc = R.T @ (Pw - t)

    Xc = Pc[0, 0]
    Yc = Pc[1, 0]
    Zc = Pc[2, 0]

    # Kamera önünde mi?
    if Zc <= 0.001:
        return 0.0, 0.0, False

    # 3) Normalize edilmiş görüntü düzlemi
    x = Xc / Zc
    y = -Yc / Zc   # Görüntü koordinatında Y ekseni ters

    # 4) Görüntü bozulması
    k1 = cam.k1
    k2 = cam.k2
    k3 = cam.k3
    p1 = cam.p1
    p2 = cam.p2

    r2 = x*x + y*y
    radial = 1 + k1*r2 + k2*(r2**2) + k3*(r2**3)

    x_d = x * radial + 2*p1*x*y + p2*(r2 + 2*x*x)
    y_d = y * radial + p1*(r2 + 2*y*y) + 2*p2*x*y

    # 5) Kamera iç parametreleri
    u = cam.fx * x_d + cam.cx
    v = cam.fy * y_d + cam.cy

    return float(u), float(v), True
