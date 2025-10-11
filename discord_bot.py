import datetime
import os
from typing import List, Tuple

import discord
from discord.abc import GuildChannel


def message2str(message: 'discord.message.Message') -> str:
    #TODO manage mentions
    return f"{message.author.display_name}: {message.clean_content}"


class DiscordBot:
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        self.client = discord.Client(intents=intents)

    def run(self):
        self.client.run(os.environ['DISCORD_TOKEN'])

    async def channel_history(self, channel_id: int = None, channel: GuildChannel = None, after: datetime.datetime = None) -> Tuple[List[str], datetime.datetime]:
        if channel is None:
            if channel_id is None:
                channel_id = int(os.environ['DISCORD_CHANNEL_ID'])
            channel = self.client.get_channel(channel_id)
        #TODO manage pagination
        messages = [message async for message in channel.history(oldest_first=True, after=after)]

        last_time = messages[-1].created_at
        return [message2str(m) for m in messages], last_time