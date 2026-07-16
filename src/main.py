"""The core logic of the app."""

import discord
from discord import app_commands

from src import config

from .command_groups import CMD_GROUPS
from .config import Config

CONFIG = Config()


class MyClient(discord.Client):
    user: discord.ClientUser

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # instant registeration of commands
        if CONFIG.my_guild:
            g = discord.Object(id=CONFIG.my_guild)

            self.tree.copy_global_to(guild=g)
            await self.tree.sync(guild=g)

    async def on_ready(self):
        print(f"Logged on as {self.user}")


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
for CMDGroup in CMD_GROUPS:
    client.tree.add_command(CMDGroup(client=client, config=CONFIG))
