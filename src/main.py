"""The core logic of the app."""

import discord
from discord import app_commands as apc

from src import config, db
from src.utils import embed_status

from .command_groups import CMD_GROUPS
from .config import Config

CONFIG = Config()


class MyClient(discord.Client):
    user: discord.ClientUser

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = apc.CommandTree(self)

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


@client.tree.command(description="Mark a module as checked")
@apc.describe(module="The module to check")
async def check(interaction: discord.Interaction, module: str):
    status = db.create_entry(interaction.user.id, int(module))
    await interaction.response.send_message(embed=embed_status(status), ephemeral=True)


@check.autocomplete("module")
async def check_autocomplete_module(
    interaction: discord.Interaction, current: str
) -> list[apc.Choice[str]]:
    return [
        apc.Choice(
            name=f"{module['courseName']} — {module['name']}"  # not in a default channel
            if "courseName" in module.keys()
            else module["name"],  # in a default channel
            value=str(module["id"]),
        )
        for module in db.get_modules_state(interaction.user.id, interaction.channel_id)
        if module["name"].lower().startswith(current.lower())
        or module["courseName"].lower().startswith(current.lower())
    ][:25]


@client.tree.command(description="Uncheck a module")
@apc.describe(module="The module to uncheck")
async def uncheck(interaction: discord.Interaction, module: str):
    status = db.delete_entry(interaction.user.id, int(module))
    await interaction.response.send_message(embed=embed_status(status), ephemeral=True)


@uncheck.autocomplete("module")
async def uncheck_autocomplete_module(
    interaction: discord.Interaction, current: str
) -> list[apc.Choice[str]]:
    return [
        apc.Choice(
            name=f"{module['courseName']} — {module['name']}"  # not in a default channel
            if "courseName" in module.keys()
            else module["name"],  # in a default channel
            value=str(module["id"]),
        )
        for module in db.get_modules_state(
            interaction.user.id, interaction.channel_id, checked_only=True
        )
        if module["name"].lower().startswith(current.lower())
        or module["courseName"].lower().startswith(current.lower())
    ][:25]
