import json
import os

class ExperienceManager:
    def __init__(self, db_path="experience.json"):
        self.db_path = db_path
        self.memory = self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {}

    def save_success(self, context, payload):
        if context not in self.memory:
            self.memory[context] = []
        if payload not in self.memory[context]:
            self.memory[context].append(payload)
            self._save()

    def _save(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.memory, f)

    def get_successful_payloads(self, context):
        return self.memory.get(context, [])
