from src.fsm.state import BaseState
from src.app.device_orchestrator import DeviceOrchestrator


class InitDevicesState(BaseState):
    def on_enter(self):
        print("[InitDevicesState] Başlıyor...")

        try:
            orchestrator = DeviceOrchestrator(self.manager.ctx)
            orchestrator.init_all()
        except Exception as e:
            print(f"[InitDevicesState] Hata: {e}")
            self.manager.stop()
            return

        from src.fsm.states.ui_state import UiState

        print("[InitDevicesState] UiState'e geçiliyor...")
        self.manager.change_state(UiState(self.manager))
