"""Discord bot for supporting functionality of misc fetcher and strip_checker"""

# import platform
import asyncio
import functools
import pathlib
import sys
import os
import subprocess
import discord

# pylint: disable=wrong-import-order
# from typing import Optional
from dotenv import load_dotenv
from discord import app_commands


load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MY_GUILD = discord.Object(id=396357106216861708)  # replace with your guild id

if not DISCORD_TOKEN:
    print('No discord token in environment')
    sys.exit()

# pylint: disable=redefined-outer-name


class MyClient(discord.Client):
    """Main bot class"""

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    """Fires this function when bot is ready"""
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@client.tree.command()
@app_commands.describe(username="The PIMD username who's misc you wanted to see")
async def misc(interaction: discord.Interaction, username: str):
    """Calculates misc and returns"""

    loop = asyncio.get_event_loop()
    await interaction.response.defer()

    path = pathlib.Path(os.getcwd()) / '..'

    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, ['py', 'misc_fetcher.py', '-Hu', username],
                                                               capture_output=True, encoding='utf-8', cwd=path))

    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(e)
        return await interaction.followup.send('An error occurred.')

    await interaction.followup.send(f"```\n{c.stdout}```")


@client.tree.command()
@app_commands.describe(hits="Total number of hits done", percentage="What percent cash is being taken", total="Total cash taken")
async def hits(interaction: discord.Interaction, hits: int, percentage: float, total: str):
    """Calculates the cash lost and left"""

    loop = asyncio.get_event_loop()
    await interaction.response.defer()

    path = pathlib.Path(os.getcwd()) / '..'

    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, ['py', 'hits.py', str(hits), str(percentage), total],
                                                               capture_output=True, encoding='utf-8', cwd=path))

    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(e)
        return await interaction.followup.send('An error occurred.')

    await interaction.followup.send(f"```\n{c.stdout}```")


@client.tree.command()
@app_commands.describe(ally="Comma seperated list of allies to add.")
async def add_ally(interaction: discord.Interaction, ally: str):
    """Adds allies to the database"""

    loop = asyncio.get_event_loop()
    allies = [x.strip() for x in ally.split(',')]

    cmd = ['py', 'add_ally.py', '-u']
    cmd.extend(allies)

    path = pathlib.Path(os.getcwd()) / '..'

    await interaction.response.defer()

    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, cmd,
                                                               capture_output=True, encoding='utf-8', cwd=path))

    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(e)
        return await interaction.followup.send('An error occurred.')

    await interaction.followup.send(f"```\n{c.stdout}```")

client.run(DISCORD_TOKEN)
