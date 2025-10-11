from discord_bot import DiscordBot
from game_state import GameState
from llm import Gemini


async def update_history(state: GameState, history_coroutine):
    history, last_time = await history_coroutine
    state.history = history
    state.save()


async def init_game_state(state: GameState):
    loaded = state.load()
    if not loaded:
        await update_history(state, state.bot.channel_history(state.bot.default_channel))
    state.llm.load_prompt(state.step)

async def on_ready(state: GameState):
    if state.step == 0 and len(state.history) == 0:
        await state.bot.send_message(state.get_actual_message()["start"])

async def on_message(state: GameState, message):
    bot = state.bot
    if message.channel.id != bot.default_channel:
        return

    await update_history(state, bot.channel_history(channel=message.channel))

    if message.author == bot.user:
        return

    response = state.llm.generate_content(state.history)
    await message.channel.send(response)