from dotenv import load_dotenv
from discord_bot import DiscordBot
from game_state import GameState


async def update_history(state: GameState, history_coroutine):
    history, last_time = await history_coroutine
    state.history = history
    state.last_message_time = last_time
    state.save()

def main():
    load_dotenv()

    bot = DiscordBot()
    state = GameState()
    state.load()

    @bot.client.event
    async def on_message(message):
        await update_history(state, bot.channel_history(channel = message.channel))

    bot.run()


if __name__ == '__main__':
    main()