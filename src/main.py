"""The core logic of the app."""

import functools

import discord
from discord import app_commands

from . import db as db
from .config import Config
from .utils import error_embed, info_embed

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


def admin_perms(func):
    @functools.wraps(func)
    async def wrapper(interaction: discord.Interaction, *args, **kwargs):
        user_roles: list[str] = [str(r).lower() for r in interaction.user.roles]

        if not any(
            [admin_role.lower() in user_roles for admin_role in CONFIG.admin_roles]
        ):
            await interaction.response.send_message(
                embed=error_embed(
                    "You don't have permission to use this command. Please contact an admin."
                ),
                ephemeral=True,
            )
            return

        await func(interaction, *args, **kwargs)

    return wrapper


@client.tree.command()
@app_commands.describe(name="The group's name")
@admin_perms
async def new_group(interaction: discord.Interaction, name: str):
    group_id = db.create_group(name=name)
    await interaction.response.send_message(
        embed=info_embed(f"Group: **{name}** created."), ephemeral=True
    )


@client.tree.command()
@app_commands.describe(
    group="The group that owns this course",
    name="The name of the course",
    default_channel="It won't be necessary to specify the course if in that a channel",
    order="The ordering of the course inside its group",
)
@admin_perms
async def new_course(
    interaction: discord.Interaction,
    group: int,
    name: str,
    default_channel: str | None = None,
    order: int | None = None,
):
    con = db.get_db()

    row = con.execute("SELECT * FROM courseGroup WHERE id = ?", (group,)).fetchone()

    if not row:
        await interaction.response.send_message(
            embed=error_embed("Such a group doesn't exist."), ephemeral=True
        )
        return

    channel_in_use = con.execute(
        "SELECT * FROM course where channelId = ?", (default_channel,)
    ).fetchone()
    if default_channel and channel_in_use:
        await interaction.response.send_message(
            embed=error_embed(
                f"Channel is already linked to course **{channel_in_use['name']}**."
            )
        )
        return

    course_id = db.create_course(
        group, name, int(default_channel) if default_channel else None, order
    )
    await interaction.response.send_message(
        embed=info_embed(f"Course: **{name}** created."), ephemeral=True
    )


@new_course.autocomplete("group")
async def group_choices(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    groups = db.get_all("courseGroup")
    return [
        app_commands.Choice(name=g["name"], value=g["id"])
        for g in groups
        if g["name"].lower().startswith(current.lower())
    ]


@new_course.autocomplete("default_channel")
async def channel_choices(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    channels = [
        ch for ch in interaction.guild.channels if isinstance(ch, discord.TextChannel)
    ]
    return [
        app_commands.Choice(name=ch.name, value=str(ch.id))
        for ch in channels
        if ch.name.lower().startswith(current.lower())
    ]
