from src.fsm.state import BaseState
from src.fsm.states.init_devices_state import InitDevicesState


class LoadConfigState(BaseState):
    
    
    def on_enter(self): 
        print("[LoadConfigState] -> Çalışmaya Başladı")
        try:
            config_manager = self.manager.ctx.config
            config_manager.load_all_json()
        except Exception as e:
            print("[LoadConfigState] -> Konfigürasyon yüklenemedi:", e)
            self.manager.stop()
            return
            
        print("[LoadConfigState] Konfigürasyonlar hazır")
        self.manager.change_state(InitDevicesState(self.manager))

    def update(self):
        print("[LoadConfigState] -> Güncellendi")

    def on_exit(self):
        pass
