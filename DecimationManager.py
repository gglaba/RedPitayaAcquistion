import json, pathlib

class DecimationManager:
    def __init__(self, path="decimations.json"):
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

    def get_dict(self):
        return dict(self.data)

    def save(self, name, value):
        self.data[name] = value
        self.path.write_text(json.dumps(self.data, indent=2))

    def delete(self, name):
        if name in self.data:
            del self.data[name]
            self.path.write_text(json.dumps(self.data, indent=2))