import json
import os
import time

class StatusTracker:
    def __init__(self, execution_dir):
        self.execution_dir = execution_dir
        self.status_file = os.path.join(execution_dir, 'status.json')
        self.steps = {
            "crawl": {"label": "Buscando vídeos no YouTube", "status": "pending"},
            "download": {"label": "Baixando conteúdo", "status": "pending"},
            "comments": {"label": "Extraindo comentários", "status": "pending"},
            "audio": {"label": "Processando áudio", "status": "pending"},
            "analyze": {"label": "Análise estratégica com IA", "status": "pending"},
            "complete": {"label": "Relatório finalizado", "status": "pending"}
        }
        self._save()

    def update_step(self, step_id, status, message=None):
        """status: pending, running, success, error"""
        if step_id in self.steps:
            self.steps[step_id]["status"] = status
            if message:
                self.steps[step_id]["message"] = message
            self._save()

    def _save(self):
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_update": time.time(),
                    "steps": self.steps
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving status: {e}")

    @staticmethod
    def get_status(execution_dir):
        status_file = os.path.join(execution_dir, 'status.json')
        if os.path.exists(status_file):
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
