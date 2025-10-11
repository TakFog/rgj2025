import asyncio

from dotenv import load_dotenv

import game_logic
from discord_bot import DiscordBot
from game_logic import init_game_state
from game_state import GameState
from llm import Gemini
from notion_pages_updater import NotionPagesDB

def main():
    load_dotenv()

    bot = DiscordBot()
    llm = Gemini("gemini-2.0-flash-lite")
    notionPages = NotionPagesDB()
    state = GameState(bot=bot, llm=llm, notion=notionPages)

    @bot.client.event
    async def on_ready():
        await init_game_state(state)
        await game_logic.on_ready(state)

    @bot.client.event
    async def on_message(message):
        if message.channel.id == bot.default_channel:
            await game_logic.on_message(state, message)

    bot.run()


if __name__ == '__main__':
    main()