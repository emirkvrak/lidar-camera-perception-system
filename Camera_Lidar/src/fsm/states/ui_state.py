# src/fsm/states/ui_state.py

from src.fsm.state import BaseState
from src.fsm.states.shutdown_state import ShutdownState
from src.ui.viewer.viewer_main import ViewerMain


class UiState(BaseState):
    def on_enter(self):
        print("[UiState] Viewer başlatılıyor")

        self.viewer = ViewerMain(
            camera_projection=self.manager.ctx.systems.camera_projection,
            lidar_projection=self.manager.ctx.systems.lidar_projection,
            camera_service=self.manager.ctx.services.camera,
            lidar_service=self.manager.ctx.services.lidar,
            config_manager=self.manager.ctx.config,
            on_close=lambda: self.manager.change_state(ShutdownState(self.manager)),
        )

        self.viewer.start()
