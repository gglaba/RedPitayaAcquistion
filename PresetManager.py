import json, pathlib

class PresetManager:
    def __init__(self, path="presets.json"):
        self.path = pathlib.Path(path)
        self.path.touch(exist_ok=True)
        self._load()

    def _load(self):
        try:
            self.data = json.loads(self.path.read_text() or "{}")
        except json.JSONDecodeError:
            self.data = {}

    def names(self):
        return list(self.data)
    def load(self, name):
        return self.data.get(name, {})
    def save(self, name, params: dict):
        # Validate params
        required_keys = ["Decimation", "Buffer size", "Delay", "Loops", "Time"]
        for key in required_keys:
            if key not in params:
                print(f"Warning: Missing key '{key}' in preset data")  # Debugging statement
        self.data[name] = params
        self.path.write_text(json.dumps(self.data, indent=2))
