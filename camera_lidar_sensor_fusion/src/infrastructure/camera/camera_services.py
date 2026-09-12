
from typing import List


class CameraService:


    def __init__(self):
        self.cameras: List[object] = []

    def start(self):
        self.start_all()

    def start_all(self):
        print(
            "[CameraService] Fiziksel kamera sürücüsü paylaşılmadı; "
            "sanal siyah kamera ekranları kullanılacak"
        )

    def shutdown(self):
        self.cameras.clear()

    def stop(self):
        self.shutdown()
