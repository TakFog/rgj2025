from dotenv import load_dotenv
from discord_bot import DiscordBot
from game_state import GameState
from llm import Gemini


async def update_history(state: GameState, history_coroutine):
    history, last_time = await history_coroutine
    state.history = history
    state.last_message_time = last_time
    state.save()

def main():
    load_dotenv()

    bot = DiscordBot()
    state = GameState()
    llm = Gemini("gemini-2.0-flash-lite")

    state.load()
    llm.load_prompt(state.step)

    @bot.client.event
    async def on_message(message):
        await update_history(state, bot.channel_history(channel = message.channel))

        if message.author == bot.user:
            return

        response = llm.generate_content(state.history)
        await message.channel.send(response)

    bot.run()


if __name__ == '__main__':
    main()