import asyncio
import os

from src.infrastructure.lidar.lidar_stream import decode_lidar_stream
from src.core.projection.lidar_projection_system import LidarProjectionSystem


class LidarDriver:
    """
    lidar.data veri oynatma sürücüsü:
    - decode_lidar_stream ile dosyadan kare okur
    - LidarProjectionSystem ile dünya dönüşümü ve filtre uygular
    - sonucu arayüz tarafına aktarır
    """

    def __init__(
        self,
        device_index: int,
        file_path: str,
        lidar_projection: LidarProjectionSystem,
        on_points: callable,
        fps: float = 10.0,
        loop_forever: bool = True,
        debug: bool = True,
        debug_every_n: int = 30,
    ):
        self.device_index = device_index
        self.file_path = file_path
        self.lidar_projection = lidar_projection
        self.on_points = on_points

        self._running = True
        self._fps = float(fps)
        self._dt = 1.0 / self._fps if self._fps > 0 else 0.1
        self._loop_forever = bool(loop_forever)

        self.debug = bool(debug)
        self.debug_every_n = max(int(debug_every_n), 1)

    async def run_async(self):
        print("[LidarDriver] lidar.data veri oynatma başladı")
        print(f"[LidarDriver] path   = {self.file_path}")
        print(f"[LidarDriver] exists = {os.path.exists(self.file_path)}")

        frame_index = 0

        try:
            while self._running:
                any_frame = False

                for ts, frame in decode_lidar_stream(self.file_path):
                    if not self._running:
                        break

                    frame_index += 1
                    any_frame = True

                    cart = frame["cartesian"]
                    photons = frame["photon_count"]
                    dirs = frame.get("direction_id", None)

                    world_pts, _, _ = self.lidar_projection.project_and_filter(
                        cartesian=cart,
                        photon_count=photons,
                        direction_id=dirs,
                    )

                    # Noktaları servise aktar.
                    self.on_points(world_pts)

                    # Arada bir durum bilgisini yazdır.
                    if self.debug and (frame_index % self.debug_every_n == 0):
                        print(f"[LidarDriver] FRAME {frame_index} | ts={ts:.3f}")
                        print(f"[LidarDriver] ham noktalar    : {cart.shape}")
                        print(f"[LidarDriver] dünya noktaları : {world_pts.shape}")
                        if world_pts.size > 0:
                            p0 = world_pts[0]
                            print(
                                f"[LidarDriver] ilk nokta → "
                                f"x={p0[0]:.2f}, y={p0[1]:.2f}, z={p0[2]:.2f}"
                            )
                        else:
                            print("[LidarDriver] dünya noktaları boş")

                    await asyncio.sleep(self._dt)

                if not self._loop_forever:
                    break

                if not any_frame:
                    await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            print("[LidarDriver] asyncio.CancelledError (task iptal)")
        except Exception as e:
            print("[LidarDriver][KRİTİK] hata:", repr(e))
        finally:
            print("[LidarDriver] durduruldu")

    def stop(self):
        self._running = False

    @staticmethod
    def get_lidar_count() -> int:
        return 1
