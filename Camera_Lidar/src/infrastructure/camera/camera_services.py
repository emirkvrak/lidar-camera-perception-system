import threading
import asyncio
from typing import List, Optional



class CameraService:
    def __init__(self):
        self.cameras = []
        self._loop = asyncio.new_event_loop()
        self._tasks: List[asyncio.Future] = []

        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True
        )
        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def start(self):
        self.start_all()

    def start_all(self):

        
        # MVS içerisinden USB ye bağlı kameraları bulmak için eriştik
        from src.infrastructure.camera.camera_driver import CameraDriver
        from src.core.mvs.CameraParams_const import MV_GIGE_DEVICE, MV_USB_DEVICE
        from src.core.mvs.MvCameraControl_class import MvCamera
        from src.core.mvs.CameraParams_header import MV_CC_DEVICE_INFO_LIST

        device_list = MV_CC_DEVICE_INFO_LIST()
        ret = MvCamera.MV_CC_EnumDevices(
            MV_GIGE_DEVICE | MV_USB_DEVICE,
            device_list
        )

        if ret != 0 or device_list.nDeviceNum == 0:
            print("[CameraService] Kamera bulunamadı")
            return

        cam_count = device_list.nDeviceNum

        for idx in range(cam_count):
            cam = CameraDriver(device_index=idx)
            cam.open_camera()
            cam.turn_camera_to_interior_mode()
            cam.start_grabbing()

            fut = asyncio.run_coroutine_threadsafe(
                cam.run_async(),
                self._loop
            )

            self._tasks.append(fut)
            self.cameras.append(cam)

    def get_camera(self, index: int):
        if 0 <= index < len(self.cameras):
            return self.cameras[index]
        return None

    def shutdown(self):
        for cam in self.cameras:
            cam._should_exit = True
            #MVS nin içinde kamera kapatmak için

        for fut in self._tasks:
            try:
                fut.cancel()
            except Exception:
                pass

        self._tasks.clear()
        self.cameras.clear()

        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread.is_alive():
            self._thread.join(timeout=1)

    
    def stop(self):
        self.shutdown()