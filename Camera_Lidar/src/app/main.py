from src.fsm.state_manager import StateManager
from src.fsm.states.load_config_state import LoadConfigState


class Main:

    def main():
        print("[Main] Uygulama başlatılıyor")

        state_manager = StateManager()

        try:
            state_manager.change_state(LoadConfigState(state_manager))
            state_manager.run()
        except KeyboardInterrupt:
            print("[Main] Kullanıcı tarafından durduruldu")
        finally:
            print("[Main] Uygulama kapatıldı")


    if __name__ == "__main__":
        main()