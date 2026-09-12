from typing import Dict
import os , json


class ConfigRepository:

    def __init__(self, path:str, default_data:Dict):
        self.path = path
        self.default_data= default_data

    def load_from_json(self) -> Dict:

        if not os.path.exists(self.path):
            print(f"[ConfigRepository] Eksik → {self.path}, default oluşturuluyor")
            self.save_write_json(self.default_data)
            return self.default_data

        try:
            with open(self.path, "r", encoding="utf-8") as rjson:
                return json.load(rjson)
        except Exception as e:
            print(f"[ConfigRepository] Bozuk JSON formatı→ {self.path} ({e})")

            try:
                backup_path = self.path + ".buckup"
                os.rename(self.path, backup_path)
                print(f"[ConfigRepository] Yedeklendi → {self.path}.backup")
            except Exception as be:
                print(f"[ConfigRepository] Backup alınamadı: {be}")
            
            self.save_write_json(self.default_data)
            return self.default_data

    def save_write_json(self, data: Dict) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp_path = self.path + ".tmp"

        with open(tmp_path, "w", encoding="utf-8") as wjson:
            json.dump(data, wjson, indent=4)

        os.replace(tmp_path,self.path)