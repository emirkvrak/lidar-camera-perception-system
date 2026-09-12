from typing import Dict, Protocol

class Service(Protocol):
    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...


class ServicesRegestry:
    def __init__(self):
        self._services: Dict[str, Service] = {}


    def register(self, name: str, service: Service):
        print(f"[ServicesRegistry] Servis kayıt edildi: {name}")
        self._services[name] = service


    def stop_all(self):
        for name, service in self._services.items():
            print(f"[ServicesRegistry] Servis durduruluyor: {name}")
            
            try:
                service.stop()
            except Exception as e:
                print(f"[ServicesRegistry] Servis durdurulamadı: {name} ({e})")