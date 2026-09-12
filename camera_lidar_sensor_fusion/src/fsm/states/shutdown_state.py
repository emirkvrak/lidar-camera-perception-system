from src.fsm.state import BaseState

class ShutdownState(BaseState):
    def on_enter(self):
        print("[ShutdownState] Uygulama kapatılıyor...")

        self.manager.ctx.services_registry.stop_all()
        self.manager.stop()
