import asyncio
import datetime
from typing import List, Tuple

import requests

from game_state import GameState
from hugo import gather_insights


async def update_history(state: GameState, history_coroutine):
    history, last_time = await history_coroutine
    state.history = history
    state.save()


async def init_game_state(state: GameState):
    state.load()
    await update_history(state, state.bot.channel_history(state.bot.default_channel))
    state.llm.load_prompt(state.step)

async def init_step(state: GameState, step: int):
    print("init step", step)
    state.step = step
    message = state.get_actual_message()
    notion_page = message.get("notion_nfc_page_key")
    if notion_page:
        ok, err = state.notion.active_phase(notion_page)
        if err is not None:
            print(err)
    if not state.start_sent:
        start_msg = message.get("start")
        if start_msg:
            await state.bot.send_message(start_msg, message.get("photo"))
        if "start_video" in message:
            state.video.play(message["video"])
    state.active = True
    state.start_sent = True
    state.hint_sent = False
    state.save()
    if "hint" in message:
        asyncio.create_task(wait_for_hint(state))
    if "disconnect" in message:
        asyncio.create_task(loop_disconnect(state))
    if "auto_next" in message:
        asyncio.create_task(wait_next_step(state, "auto_next"))

async def wait_time(state: GameState, start_pair: List[int], fast_wait: Tuple[int, int]):
    if state.fast_mode:
        wt = state.random.randint(*fast_wait)
    else:
        start_hour, start_minute = start_pair
        now = datetime.datetime.now()
        if now.hour > start_hour or (now.hour == start_hour and now.minute >= start_minute):
            # wait a bit
            wt = state.random.randint(2*60, 4*60)
        else:
            # wait the time
            wt = (start_hour*60 + start_minute - now.hour*60 - now.minute) * 60
    print("wait for", wt)
    await asyncio.sleep(wt)

async def wait_next_step(state: GameState, key="next_start"):
    print("wait next step", key)
    phase_config = state.get_actual_message()
    start_time = phase_config.get(key)
    if start_time is None:
        return
    last_step = state.step
    await wait_time(state, start_time, (5, 10))
    if state.step == last_step:
        await init_step(state, state.step+1)

async def wait_for_hint(state: GameState):
    if state.hint_sent:
        return
    hint_step = state.step
    phase_config = state.get_actual_message().get("hint")
    if not phase_config:
        return
    print("wait for hint")
    await wait_time(state, phase_config["start"], (20, 20))
    if hint_step != state.step or state.hint_sent or not state.active:
        return
    print("send hint", hint_step)
    await state.bot.send_message(phase_config.get("message",""), phase_config.get("photo"))
    state.hint_sent = True
    state.save()

def check_code(state: GameState, message) -> bool:
    phase_config = state.get_actual_message()
    if "code" not in phase_config:
        return False
    if phase_config["code"] not in message.content:
        return False
    print("code found in "+message.content)
    return True

async def check_hugo(state: GameState) -> bool:
    phase_config = state.get_actual_message()
    hugo = phase_config.get("hugo")
    if not hugo:
        return False
    hugo_th = phase_config.get("hugo_th", len(hugo))
    insights = gather_insights(state.history, '\n'.join(hugo))
    return sum(1 for i in insights if i.outcome) >= hugo_th

async def on_ready(state: GameState):
    if state.active:
        await init_step(state, state.step)
    else:
        await wait_next_step(state)

async def on_message(state: GameState, message):
    bot = state.bot

    if message.author == bot.user:
        return
    if not state.active or not state.start_sent:
        return

    if check_code(state, message) or check_hugo(state):
        phase_config = state.get_actual_message()
        state.active = False
        state.start_sent = False
        state.save()
        await state.bot.send_message(phase_config["success"])
        if "next_start" in phase_config:
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
    if not state.active or state.history[-1]["role"] != 'user':
        return
    response = state.llm.generate_content(state.history)
    await message.channel.send(response)

async def loop_disconnect(state: GameState):
    print("loop disconnect")
    while state.active:
        try:
            requests.get("https://www.google.com", timeout=3)
            await asyncio.sleep(1)
        except requests.ConnectionError:
            print("connection error")
            phase_config = state.get_actual_message()
            state.video.play(phase_config["disconnect"])
            state.active = False
