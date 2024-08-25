"""Discord bot for supporting functionality of misc fetcher and strip_checker"""

# import platform
import asyncio
import functools
import json
import pathlib
import sys
import os
import subprocess
import discord

# pylint: disable=wrong-import-order
# from typing import Optional
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands


load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')
MY_GUILD = discord.Object(id=int(GUILD_ID))  # replace with your guild id

if not DISCORD_TOKEN:
    print('No discord token in environment')
    sys.exit()

# pylint: disable=redefined-outer-name


class MyBot(commands.Bot):
    """Main bot class"""

    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix='$', intents=intents)
        # self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
intents.message_content = True
bot = MyBot(intents=intents)


@bot.event
async def on_ready():
    """Fires this function when bot is ready"""
    await bot.load_extension('jishaku')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@bot.tree.command()
@app_commands.describe(username="The PIMD username who's misc you wanted to see")
async def misc(interaction: discord.Interaction, username: str):
    """Calculates misc and returns it"""

    loop = asyncio.get_event_loop()
    await interaction.response.defer()

    path = pathlib.Path(os.getcwd()) / '..'

    python = path / 'venv' / 'bin' / 'python3'
    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, [python, 'misc_fetcher.py', '-Hu', username],
                                                               capture_output=True, encoding='utf-8', cwd=path))

    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(e)
        return await interaction.followup.send('An error occurred.')

    await interaction.followup.send(f"```\n{c.stdout}```")


@bot.tree.command()
@app_commands.describe(hits="Total number of hits done", percentage="What percent cash is being taken", total="Total cash taken")
async def hits(interaction: discord.Interaction, hits: int, percentage: float, total: str):
    """Calculates the cash lost and left"""

    loop = asyncio.get_event_loop()
    await interaction.response.defer()

    path = pathlib.Path(os.getcwd()) / '..'
    python = path / 'venv' / 'bin' / 'python3'
    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, [python, 'hits.py', str(hits), str(percentage), total],
                                                               capture_output=True, encoding='utf-8', cwd=path))

    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(e)
        return await interaction.followup.send('An error occurred.')

    await interaction.followup.send(f"```\n{c.stdout}```")


@bot.tree.command()
@app_commands.describe(ally="Comma seperated list of allies to add.")
async def add_ally(interaction: discord.Interaction, ally: str):
    """Adds allies to the database"""

    loop = asyncio.get_event_loop()
    allies = [x.strip() for x in ally.split(',')]

    path = pathlib.Path(os.getcwd()) / '..'

    python = path / 'venv' / 'bin' / 'python3'

    cmd = [python, 'add_ally.py', '-u']
    cmd.extend(allies)

    await interaction.response.defer()

    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, cmd,
                                                               capture_output=True, encoding='utf-8', cwd=path))

    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(e)
        return await interaction.followup.send('An error occurred.')

    await interaction.followup.send(f"```\n{c.stdout}```")


@bot.tree.command()
async def list_allies(interaction: discord.Interaction):
    """Lists allies present in the database"""

    loop = asyncio.get_event_loop()

    path = pathlib.Path(os.getcwd()) / '..'
    python = path / 'venv' / 'bin' / 'python3'
    cmd = [python, 'add_ally.py', '-Hl']

    await interaction.response.defer()

    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, cmd,
                                                               capture_output=True, encoding='utf-8', cwd=path))

    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(e)
        return await interaction.followup.send('An error occurred.')

    ally_list = json.loads(c.stdout.replace("'", '"'))
    ally_list = ', '.join(ally_list)

    await interaction.followup.send(f"```\n{ally_list}```")

@bot.tree.command()
@app_commands.describe(ally="Comma seperated list of allies to add.")
async def stop_watching(interaction: discord.Interaction, ally: str):
    """Stops the bot from watching given username(s)"""

    loop = asyncio.get_event_loop()
    allies = [x.strip() for x in ally.split(',')]

    path = pathlib.Path(os.getcwd()) / '..'

    python = path / 'venv' / 'bin' / 'python3'

    cmd = [python, 'stop_watching.py', '-u']
    cmd.extend(allies)

    await interaction.response.defer()

    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, cmd,
                                                               capture_output=True, encoding='utf-8', cwd=path))

    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(e)
        return await interaction.followup.send('An error occurred.')

    await interaction.followup.send(f"```\n{c.stdout}```")

bot.run(DISCORD_TOKEN)
