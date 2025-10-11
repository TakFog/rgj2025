import json
import os
import random
from typing import List

from discord_bot import DiscordBot
from llm import Gemini


class GameState:
    def __init__(self, llm: 'Gemini', bot: 'DiscordBot', notion: 'NotionPagesDB'):
        self.llm = llm
        self.bot = bot
        self.notion = notion
        self.step = 0
        self.active = False
        self.channel = bot.default_channel
        self.history: List[dict] = []
        self.random = random.Random()
        with open(os.path.join('msg.json'), 'r', encoding="utf8") as f:
            self.messages = json.load(f)

    @property
    def state_path(self):
        return os.getenv("GAME_STATE_PATH", "game_state")

    def state_file(self, channel_id):
        return os.path.join(self.state_path, "{}.json".format(channel_id))

    def get_actual_message(self):
        return self.messages[str(self.step)]

    def load(self, channel_id = None) -> bool:
        if channel_id is None:
            channel_id = self.channel
        full_path = self.state_file(channel_id)

        if not os.path.exists(full_path):
            print("Game state file not found")
            self.channel = channel_id
            return False

        with open(full_path, "r") as f:
            data = json.load(f)

        self.history = data["history"]
        self.channel = data["channel"]
        self.step = data["step"]
        self.active = data["active"]
        return True

    def save(self):
        data = {
            "channel": self.channel,
            "step": self.step,
            "active": self.active,
            "history": self.history,
        }
        os.makedirs(self.state_path, exist_ok=True)
        with open(self.state_file(self.channel), "w") as f:
            json.dump(data, f, indent=True)
