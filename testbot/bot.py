# https://discordpy.readthedocs.io/en/stable/quickstart.html
# This example requires the 'message_content' intent.

import discord
import os
from dotenv import load_dotenv
from google import genai
import asyncio

class Llm:
    def __init__(self, model: str):
        self.model = model
        # The client gets the API key from the environment variable `GEMINI_API_KEY`.
        self.aiclient = genai.Client()

    def generate_content(self, input):
        response = self.aiclient.models.generate_content(
            model=self.model, contents=input
        )
        return response.text

load_dotenv('.env')

llm = Llm("gemini-2.0-flash-lite")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    # await asyncio.sleep(10)        # delay
    await history(os.environ.get('CHANNEL_ID'))
    await send_message(os.environ.get('CHANNEL_ID'), "Sono pronto!")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('$llm'):
        response = llm.generate_content(message.content[4:])
        await message.channel.send(response[:1990]) # limit 2000 chars

    if message.content.startswith('$img'):
        file = discord.File("pergamena_codex.jpg", filename="pergamena.jpg")
        await message.channel.send("Here's an image!", file=file)


async def history(channel_id):
    global client
    if channel_id is None:
        return
    channel = client.get_channel(int(channel_id))
    history = [message async for message in channel.history(oldest_first=True)]
    history2 = [message async for message in channel.history(oldest_first=True, after=history[-3].created_at)]
    text_hist = [f"{x.author.display_name}: {x.clean_content}" for x in history]
    for text in text_hist:
        print(text)


async def send_message(channel_id, message):
    global client
    if channel_id is None:
        return
    channel = client.get_channel(int(channel_id))
    history = [message async for message in channel.history(oldest_first=True)]
    text_hist = [f"{x.author.display_name}: {x.content}" for x in history]
    for text in text_hist:
        print(text)
    await channel.send(message)

async def delayed_startup(channel_id, message):
    global client
    await asyncio.sleep(10)        # delay
    await client.wait_until_ready()   # wait until bot is ready
    print("Running delayed startup code...")
    await send_message(channel_id, message)


client.run(os.environ['DISCORD_TOKEN'])
