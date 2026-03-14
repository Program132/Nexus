import os
import json
from datetime import datetime

class Workspace:
    def __init__(self, name: str, is_new: bool, save_enabled: bool):
        self.name = name
        self.is_new = is_new
        self.save_enabled = save_enabled
        self.active_session_id = None
        self.sessions = {}
        self.history = []
        self.notes = []
        self.env = {}
        self.ovpn = {}
        self.server = {}
        self._state_file = os.path.join(os.getcwd(), "workspaces", name, ".nexus_state.json")

    def load(self):
        if not os.path.exists(self._state_file):
            return
        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.sessions = data.get("sessions", {})
            self.history = data.get("history", [])
            self.notes = data.get("notes", [])
            self.env = data.get("env", {})
            self.ovpn = data.get("ovpn", {})
            self.server = data.get("server", {})
        except Exception:
            pass

    def save(self):
        try:
            os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump({
                    "sessions": self.sessions,
                    "history": self.history,
                    "notes": self.notes,
                    "env": self.env,
                    "ovpn": self.ovpn,
                    "server": self.server,
                    "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
