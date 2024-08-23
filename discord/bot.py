"""Discord bot for supporting functionality of misc fetcher and strip_checker"""

# import platform
import asyncio
import functools
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
    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, ['py', 'misc_fetcher.py', '-Hu', username],
                                                               capture_output=True, encoding='utf-8', cwd=os.getcwd()+'\\..'))

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
    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, ['py', 'hits.py', str(hits), str(percentage), total],
                                                               capture_output=True, encoding='utf-8', cwd=os.getcwd()+'\\..'))

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
    await interaction.response.defer()
    try:
        c = await loop.run_in_executor(None, functools.partial(subprocess.run, cmd,
                                                               capture_output=True, encoding='utf-8', cwd=os.getcwd()+'\\..'))

    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(e)
        return await interaction.followup.send('An error occurred.')

    await interaction.followup.send(f"```\n{c.stdout}```")


# @app_commands.describe(
#     first_value='The first value you want to add something to',
#     second_value='The value you want to add to the first value',
# )
# async def add(interaction: discord.Interaction, first_value: int, second_value: int):
#     """Adds two numbers together."""
#     await interaction.response\
#         .send_message(f'{first_value} + {second_value} = {first_value + second_value}')
# # The rename decorator allows us to change the display of the parameter on Discord.
# # In this example, even though we use `text_to_send` in the code, the client will use `text` instead
# # Note that other decorators will still refer to it as `text_to_send` in the code.
# @client.tree.command()
# @app_commands.rename(text_to_send='text')
# @app_commands.describe(text_to_send='Text to send in the current channel')
# async def send(interaction: discord.Interaction, text_to_send: str):
#     """Sends the text into the current channel."""
#     await interaction.response.send_message(text_to_send)
# # To make an argument optional, you can either give it a supported default argument
# # or you can mark it as Optional from the typing standard library. This example does both.
# @client.tree.command()
# @app_commands.describe(member='The member you want to get the joined date from; defaults to the user who uses the command')
# async def joined(interaction: discord.Interaction, member: Optional[discord.Member] = None):
#     """Says when a member joined."""
#     # If no member is explicitly provided then we use the command user here
#     member = member or interaction.user
#     # The format_dt function formats the date time into a human readable representation in the official client
#     await interaction.response.send_message(f'{member} joined {discord.utils.format_dt(member.joined_at)}')
# # A Context Menu command is an app command that can be run on a member or on a message by
# # accessing a menu within the client, usually via right clicking.
# # It always takes an interaction as its first parameter and a Member or Message as its second parameter.
# # This context menu command only works on members
# @client.tree.context_menu(name='Show Join Date')
# async def show_join_date(interaction: discord.Interaction, member: discord.Member):
#     # The format_dt function formats the date time into a human readable representation in the official client
#     await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}')
# # This context menu command only works on messages
# @client.tree.context_menu(name='Report to Moderators')
# async def report_message(interaction: discord.Interaction, message: discord.Message):
#     # We're sending this response message with ephemeral=True, so only the command executor can see it
#     await interaction.response.send_message(
#         f'Thanks for reporting this message by {message.author.mention} to our moderators.', ephemeral=True
#     )
#     # Handle report by sending it into a log channel
#     log_channel = interaction.guild.get_channel(
#         0)  # replace with your channel id
#     embed = discord.Embed(title='Reported Message')
#     if message.content:
#         embed.description = message.content
#     embed.set_author(name=message.author.display_name,
#                      icon_url=message.author.display_avatar.url)
#     embed.timestamp = message.created_at
#     url_view = discord.ui.View()
#     url_view.add_item(discord.ui.Button(label='Go to Message',
#                       style=discord.ButtonStyle.url, url=message.jump_url))
#     await log_channel.send(embed=embed, view=url_view)
client.run(DISCORD_TOKEN)
