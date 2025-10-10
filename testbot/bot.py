# https://discordpy.readthedocs.io/en/stable/quickstart.html
# This example requires the 'message_content' intent.

import discord
import os
from dotenv import load_dotenv
from google import genai

load_dotenv('.env')

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
aiclient = genai.Client()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('$llm'):
        response = aiclient.models.generate_content(
            model="gemini-2.0-flash-lite", contents=message.content[4:]
        )
        await message.channel.send(response.text[:1990]) # limit 2000 chars

client.run(os.environ['DISCORD_TOKEN'])
