import asyncio
import datetime
from typing import List, Tuple

from game_state import GameState


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
    state.hint_sent = False
    state.save()
    if "hint" in message:
        asyncio.create_task(wait_for_hint(state))

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

async def wait_next_step(state: GameState):
    phase_config = state.get_actual_message()
    await wait_time(state, phase_config["next_start"], (5, 10))
    await init_step(state, state.step+1)

async def wait_for_hint(state: GameState):
    hint_step = state.step
    phase_config = state.get_actual_message()["hint"]
    await wait_time(state, phase_config["start"], (60, 70))
    if hint_step != state.step or state.hint_sent or not state.active:
        return
    await state.bot.send_message(phase_config.get("message",""), phase_config.get("photo"))
    state.hint_sent = True

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
    if not state.active or  state.history[-1]["role"] != 'user':
        return
    response = state.llm.generate_content(state.history)
    await message.channel.send(response)