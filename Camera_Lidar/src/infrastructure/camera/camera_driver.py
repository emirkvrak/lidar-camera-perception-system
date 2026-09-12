import asyncio
import ctypes as ct
from time import time, sleep
from typing import Optional, Callable

import cv2
import numpy as np
import numpy.typing as npt
import threading

from src.core.mvs.CameraParams_const import MV_GIGE_DEVICE, MV_USB_DEVICE
from src.core.mvs.CameraParams_header import (MV_CC_DEVICE_INFO,
                                              MV_CC_DEVICE_INFO_LIST,
                                              MV_FRAME_OUT_INFO_EX, MVCC_ENUMVALUE,
                                              MVCC_FLOATVALUE, MVCC_INTVALUE,
                                              PixelType_Gvsp_Mono8,
                                              PixelType_Gvsp_RGB8_Packed)
from src.core.mvs.MvCameraControl_class import MV_OK, MvCamera
from src.core.enums import CameraParameter, CameraSceneType
from src.domain.base.transformable_model import TransformableModel
from src.core.constants import FRAME_TIMEOUT


class CameraDriver(TransformableModel):
    device_index = 0  # <<< EKLENDİ - çoklu kamera için sayaç

    __camera_parameter_type_map = {
        CameraParameter.AcquisitionFrameRateEnable: bool,
        CameraParameter.AcquisitionFrameRate: float,
        CameraParameter.Gamma: float,
        CameraParameter.Gain: float,
        CameraParameter.BlackLevelEnable: bool,
        CameraParameter.BlackLevel: int,
        CameraParameter.ExposureTime: float,
        CameraParameter.PixelFormat: str,
        CameraParameter.DigitalShiftEnable: bool,
        CameraParameter.DigitalShift: float,
        CameraParameter.Sharpness: int,
        CameraParameter.SharpnessEnable: bool,
        CameraParameter.OffsetY: int,
        CameraParameter.Height: int,
        CameraParameter.Width: int,
        CameraParameter.PayloadSize: int,
    }

    @property
    def is_opened(self) -> bool:
        return self.__is_opened

    @property
    def is_grabbing(self) -> bool:
        return self.__is_grabbing

    def __init__(self, device_index=None):
        self.device_index = device_index
        TransformableModel.__init__(self)

        # ---- ASENKRON ÇIKIŞ FLAG'I ----
        self._should_exit = False

        self.__thread_lock = threading.Lock()
        self.focal_length = np.array([9700, 9000], dtype=np.int32)
        self.principal_point = np.array([2048, 1000], dtype=np.int32)
        self.offset = np.array([40, 245], dtype=np.int32)
        self.width: int = 0
        self.height: int = 0
        self.__is_opened: bool = False
        self.__is_grabbing: bool = False
        self.__mv_camera: MvCamera = MvCamera()
        self.__color_conversion = cv2.COLOR_BGR2RGB  # type: ignore
        self.__was_camera_opened = False
        self.frame: npt.NDArray[np.uint8] = np.zeros((0, 0, 3), dtype=np.uint8)
        self.timestamp: float = 0.0
        self.payload_buffer: Optional[ct.Array] = None
        self.channels: int = 3
        self.hertz = 0.0
        self.camera_scene_type = CameraSceneType.LIGHT
        self.calibration_positions = np.zeros((0, 2), dtype=np.float32)
        self.on_frame_captured: Optional[Callable[[npt.NDArray, int], None]] = None
        self.frame_index = 0

        self.__device_index = CameraDriver.device_index  # <<< EKLENDİ - bu instance hangi kamerayı kullanacak
        CameraDriver.device_index += 1                   # <<< EKLENDİ

        try:
            self.__running_loop = asyncio.get_running_loop()  # <<< DEĞİŞTİRİLDİ
        except RuntimeError:
            self.__running_loop = None                        # <<< EKLENDİ

    async def run_async(self):
        """
        Kamera frame toplama coroutine'i.
        _should_exit True olduğunda veya task cancel edildiğinde
        düzgün şekilde çıkar.
        """
        if self.__running_loop is None:
            self.__running_loop = asyncio.get_running_loop()

        try:
            while not self._should_exit:
                # Kamera kapalıysa / grabbing yoksa bekle
                if not self.__is_opened or not self.__is_grabbing:
                    await asyncio.sleep(0.05)
                    continue

                def blocking():
                    # Bu fonksiyon threadpool içinde bloklayıcı şekilde frame çeker
                    while (not self._should_exit
                           and self.__is_opened
                           and self.__is_grabbing):
                        try:
                            frame = self.__get_frame()
                            if frame is not None:
                                with self.__thread_lock:
                                    self.frame = frame
                                    self.timestamp = time()
                                break
                        except Exception:
                            sleep(0.001)

                # Bloklayıcı kısmı executor'da çalıştır
                await self.__running_loop.run_in_executor(None, blocking)

                if self._should_exit:
                    break

                self.frame_index += 1
                if self.on_frame_captured is not None:
                    self.on_frame_captured(self.frame, self.frame_index)

                await asyncio.sleep(0.001)

        except asyncio.CancelledError:
            # Task iptal edilirse sessizce çık
            pass

    def open_camera(self) -> "CameraDriver":
        if self.__is_opened:
            return self
        self.__is_opened = False
        if not self.__was_camera_opened:
            self.__device_list = MV_CC_DEVICE_INFO_LIST()
            if MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, self.__device_list) != MV_OK:
                return self
            if self.__device_list.nDeviceNum == 0:
                return self

            if self.__device_index >= self.__device_list.nDeviceNum:      # <<< EKLENDİ - varsa o indexte cihaz yoksa abort
                return self

            self.__cc_info = ct.cast(
                self.__device_list.pDeviceInfo[self.__device_index],      # <<< DEĞİŞTİRİLDİ (0 → self.__device_index)
                ct.POINTER(MV_CC_DEVICE_INFO)
            ).contents
            self.__was_camera_opened = True

        if self.__mv_camera.MV_CC_CreateHandle(self.__cc_info) != MV_OK:
            return self
        if self.__mv_camera.MV_CC_OpenDevice() != MV_OK:
            return self

        self.try_set_value(CameraParameter.OffsetY, 1000)
        self.try_set_value(CameraParameter.Height, 2000)
        self.try_set_value(CameraParameter.AcquisitionFrameRate, 13.0)
        self.try_set_value(CameraParameter.AcquisitionFrameRateEnable, True)
        self.width = int(self.__get_value(CameraParameter.Width) or 0)
        self.height = int(self.__get_value(CameraParameter.Height) or 0)
        self.payload_size = int(self.__get_value(CameraParameter.PayloadSize) or 0)
        self.pixel_format = self.__get_value(CameraParameter.PixelFormat)
        self.__is_opened = True
        return self

    def close_camera(self) -> "CameraDriver":
        if not self.__is_opened:
            return self
        if self.__mv_camera.MV_CC_CloseDevice() != MV_OK:
            return self
        if self.__mv_camera.MV_CC_DestroyHandle() != MV_OK:
            return self
        self.__is_opened = False
        return self

    def try_set_value(self, camera_parameter: CameraParameter, value: float | int | str | bool):
        if camera_parameter not in self.__camera_parameter_type_map:
            return False
        value_type = self.__camera_parameter_type_map[camera_parameter]
        response = False
        if value_type == int:
            response = self.__mv_camera.MV_CC_SetIntValue(camera_parameter.value, value) == MV_OK
        elif value_type == float:
            response = self.__mv_camera.MV_CC_SetFloatValue(camera_parameter.value, value) == MV_OK
        elif value_type == str:
            response = self.__mv_camera.MV_CC_SetEnumValue(camera_parameter.value, int(value)) == MV_OK
        elif value_type == bool:
            response = self.__mv_camera.MV_CC_SetBoolValue(camera_parameter.value, value) == MV_OK
        return response

    def __get_value(self, camera_parameter: CameraParameter) -> Optional[float | int | str | bool]:
        if camera_parameter not in self.__camera_parameter_type_map:
            return None
        value_type = self.__camera_parameter_type_map[camera_parameter]
        value = None
        if value_type == int:
            value = MVCC_INTVALUE()
            self.__mv_camera.MV_CC_GetIntValue(camera_parameter.value, value)
        elif value_type == float:
            value = MVCC_FLOATVALUE()
            self.__mv_camera.MV_CC_GetFloatValue(camera_parameter.value, value)
        elif value_type == str:
            value = MVCC_ENUMVALUE()
            self.__mv_camera.MV_CC_GetEnumValue(camera_parameter.value, value)
        elif value_type == bool:
            value = MVCC_INTVALUE()
            self.__mv_camera.MV_CC_GetBoolValue(camera_parameter.value, value)
        else:
            return None
        return value.nCurValue

    def turn_camera_to_light_mode(self) -> "CameraDriver":
        self.try_set_value(CameraParameter.Gamma, 0.7)
        self.try_set_value(CameraParameter.Gain, 3.0)
        self.try_set_value(CameraParameter.ExposureTime, 900.0)
        self.try_set_value(CameraParameter.DigitalShift, 5.0)
        self.turn_pixel_format_to_rgb8_packed()
        self.camera_scene_type = CameraSceneType.LIGHT
        return self

    def turn_camera_to_dark_mode(self) -> "CameraDriver":
        self.try_set_value(CameraParameter.Gamma, 0.6)
        self.try_set_value(CameraParameter.Gain, 19.0)
        self.try_set_value(CameraParameter.ExposureTime, 600.0)
        self.try_set_value(CameraParameter.DigitalShift, 5.0)
        self.try_set_value(CameraParameter.BlackLevelEnable, True)
        self.try_set_value(CameraParameter.BlackLevel, 240)
        self.try_set_value(CameraParameter.SharpnessEnable, True)
        self.try_set_value(CameraParameter.Sharpness, 10)
        self.turn_pixel_format_to_mono8()
        self.camera_scene_type = CameraSceneType.DARK
        return self

    def turn_camera_to_interior_mode(self) -> "CameraDriver":
        self.try_set_value(CameraParameter.Gamma, 0.7)
        self.try_set_value(CameraParameter.Gain, 19.0)
        self.try_set_value(CameraParameter.ExposureTime, 30000.0)
        self.turn_pixel_format_to_rgb8_packed()
        self.camera_scene_type = CameraSceneType.INTERIOR
        return self

    def turn_pixel_format_to_rgb8_packed(self):
        self.stop_grabbing()
        if self.try_set_value(CameraParameter.PixelFormat, str(PixelType_Gvsp_RGB8_Packed)):
            self.payload_size = int(self.__get_value(CameraParameter.PayloadSize) or 0)
            self.pixel_format = self.__get_value(CameraParameter.PixelFormat)
            self.__color_conversion = cv2.COLOR_BGR2RGB  # type: ignore
        self.start_grabbing()

    def turn_pixel_format_to_mono8(self):
        self.stop_grabbing()
        if self.try_set_value(CameraParameter.PixelFormat, str(PixelType_Gvsp_Mono8)):
            self.payload_size = int(self.__get_value(CameraParameter.PayloadSize) or 0)
            self.pixel_format = self.__get_value(CameraParameter.PixelFormat)
            self.__color_conversion = cv2.COLOR_GRAY2RGB  # type: ignore
        self.start_grabbing()

    def start_grabbing(self) -> "CameraDriver":
        if not self.__is_opened or self.__is_grabbing:
            return self
        if self.__mv_camera.MV_CC_StartGrabbing() != MV_OK:
            return self
        if self.payload_size <= 0:
            return self
        with self.__thread_lock:
            self.payload_buffer = (ct.c_ubyte * self.payload_size)()
            frame_size = self.width * self.height
            self.channels = self.payload_size // frame_size if frame_size > 0 else 3
            self.__frame_out_info = MV_FRAME_OUT_INFO_EX()
            self.__is_grabbing = True
        return self

    def stop_grabbing(self) -> "CameraDriver":
        # DİKKAT: Burada _should_exit'i DEĞİŞTİRMİYORUZ
        # çünkü format değiştirme vs. sırasında stop/start yapıyoruz.
        if not self.__is_opened or not self.__is_grabbing:
            return self
        with self.__thread_lock:
            self.__mv_camera.MV_CC_StopGrabbing()
            self.__is_grabbing = False
            self.payload_buffer = None
        return self

    def __get_frame(self) -> Optional[npt.NDArray[np.uint8]]:
        if not self.__is_opened or not self.__is_grabbing or self.__mv_camera.handle is None or self.payload_buffer is None:
            return None
        try:
            with self.__thread_lock:
                if self.__mv_camera.MV_CC_GetOneFrameTimeout(self.payload_buffer, self.payload_size, self.__frame_out_info, FRAME_TIMEOUT) != MV_OK:
                    return None
                buffer_bytes = ct.string_at(self.payload_buffer, self.payload_size)
            buffer = np.frombuffer(buffer_bytes, dtype=np.uint8)
            buffer = buffer.reshape((self.height, self.width, self.channels))
            return cv2.cvtColor(buffer, self.__color_conversion).astype(np.uint8)  # type: ignore
        except Exception:
            return None

    def project(self, positions: npt.NDArray) -> npt.NDArray:
        return np.zeros((0, 2), dtype=np.int32)

    def set_focal_length(self, focal_length_x: int, focal_length_y: int) -> None:
        self.focal_length[0] = focal_length_x
        self.focal_length[1] = focal_length_y

    def set_offset(self, offset_x: int, offset_y: int) -> None:
        self.offset[0] = offset_x
        self.offset[1] = offset_y
