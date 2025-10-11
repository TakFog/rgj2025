import datetime
import json
import os
from optparse import Option
from typing import List, Optional, Tuple


class GameState:
    def __init__(self):
        self.step = 0
        self.history: List[dict] = []
        self.last_message_time: Optional[datetime.datetime] = None

    @property
    def state_path(self):
        return os.getenv("GAME_STATE_PATH", "game_state.json")

    def load(self):
        if not os.path.exists(self.state_path):
            print("Game state file not found")
            return

        with open(self.state_path, "r") as f:
            data = json.load(f)

        self.history = data["history"]
        self.step = data["step"]
        self.last_message_time = datetime.datetime.fromtimestamp(data["last_message_time"])

    def save(self):
        data = {
            "step": self.step,
            "last_message_time": self.last_message_time.timestamp(),
            "history": self.history,
        }
        with open(self.state_path, "w") as f:
            json.dump(data, f, indent=True)
