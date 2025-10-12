import json
import os
import random
from typing import List

from discord_bot import DiscordBot
from llm import Llm
from notion_pages_updater import NotionPagesDB


class GameState:
    def __init__(self, llm: 'Llm', bot: 'DiscordBot', notion: 'NotionPagesDB'):
        self.llm = llm
        self.bot = bot
        self.notion = notion
        self.step = 0
        self.active = True
        self.start_sent = False
        self.hint_sent = False
        self.fast_mode = os.environ.get('FAST_MODE', "0") == "1"
        self.channel = bot.default_channel
        self.history: List[dict] = []
        self.random = random.Random()
        with open(os.path.join('msg.json'), 'r', encoding="utf8") as f:
            self.messages = json.load(f)
        self._set_video()

    def _set_video(self):
        import video
        self.video = video.VideoPlayer()

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
        self.start_sent = data["start_sent"]
        self.hint_sent = data["hint_sent"]
        return True

    def save(self):
        print(f"save active {self.active}, start_sent {self.start_sent}, hint_sent {self.hint_sent}")
        data = {
            "channel": self.channel,
            "step": self.step,
            "active": self.active,
            "start_sent": self.start_sent,
            "hint_sent": self.hint_sent,
            "history": self.history,
        }
        os.makedirs(self.state_path, exist_ok=True)
        with open(self.state_file(self.channel), "w") as f:
            json.dump(data, f, indent=True)
