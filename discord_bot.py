import datetime
import os
from typing import List, Tuple, Any

import discord
from discord.abc import GuildChannel



class DiscordBot:
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        self.client = discord.Client(intents=intents)

    def run(self):
        self.client.run(os.environ['DISCORD_TOKEN'])

    @property
    def user(self):
        return self.client.user

    @property
    def default_channel(self):
        return int(os.environ['CHANNEL_ID'])

    async def send_message(self, message: str, file=None):
        channel = self.client.get_channel(self.default_channel)
        if file is not None:
            file = discord.File(file, filename=os.path.basename(file))
        await channel.send(message, file=file)

    async def channel_history(self, channel_id: int = None, channel: GuildChannel = None, after: datetime.datetime = None) -> Tuple[List[dict], Any]:
        if channel is None:
            if channel_id is None:
                channel_id = self.default_channel
            channel = self.client.get_channel(channel_id)
        #TODO manage pagination
        messages = [message async for message in channel.history(oldest_first=True, after=after)]

        return [self._message2context(m) for m in messages], None

    def _message2context(self, message: discord.message.Message) -> dict:
        parts = message.content
        if message.author == self.client.user:
            role = "model"
        else:
            role = "user"
            parts = f"{message.author.display_name}: {parts}"
        return {"role": role, "parts": parts}
