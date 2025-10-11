import asyncio
import datetime
import random
import threading
import time

import discord

from discord_bot import DiscordBot
from game_state import GameState
from llm import Gemini


async def update_history(state: GameState, history_coroutine):
    history, last_time = await history_coroutine
    state.history = history
    state.save()


async def init_game_state(state: GameState):
    state.load()
    await update_history(state, state.bot.channel_history(state.bot.default_channel))
    state.llm.load_prompt(state.step)

async def init_step(state: GameState, step: int):
    state.step = step
    message = state.get_actual_message()
    ok, err = state.notion.active_phase(message["notion_nfc_page_key"])
    if err is not None:
        print(err)
    await state.bot.send_message(message["start"], message.get("photo"))
    state.active = True
    state.save()

async def wait_next_step(state: GameState):
    phase_config = state.get_actual_message()
    if state.fast_mode:
        wait_time = state.random.randint(5, 10)
    else:
        start_hour, start_minute = phase_config["next_start"]
        now = datetime.datetime.now()
        if now.hour > start_hour or (now.hour == start_hour and now.minute >= start_minute):
            # wait a bit
            wait_time = state.random.randint(2*60, 4*60)
        else:
            # wait the time
            wait_time = (start_hour*60 + start_minute - now.hour*60 - now.minute) * 60
    print("wait for", wait_time)
    await asyncio.sleep(wait_time)
    await init_step(state, state.step+1)

async def on_ready(state: GameState):
    if state.step == 0 and len(state.history) == 0:
        await init_step(state, 0)
    elif not state.active:
        await wait_next_step(state)

async def on_message(state: GameState, message):
    bot = state.bot

    if message.author == bot.user:
        return
    if not state.active:
        return

    phase_config = state.get_actual_message()
    if phase_config["code"] in message.content:
        print("code found in "+message.content)
        state.active = False
        state.save()
        await state.bot.send_message(phase_config["success"])
        asyncio.create_task(wait_next_step(state))
        return

    # answer to this messsage
    if state.fast_mode:
        time = 0
    else:
        time = state.random.randint(5, 30)
    if time > 0:
        await asyncio.sleep(time)
    await update_history(state, bot.channel_history(channel=message.channel))
    if state.history[-1]["role"] != 'user':
        return
    response = state.llm.generate_content(state.history)
    await message.channel.send(response)