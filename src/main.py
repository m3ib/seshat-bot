"""The core logic of the app."""

import functools

import discord
from discord import app_commands

from . import db
from .config import Config
from .utils import embed_status, error_embed

CONFIG = Config()


class MyClient(discord.Client):
    user: discord.ClientUser

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

        # command groups
        self.admin_group = app_commands.Group(
            name="admin", description="Admin commands"
        )

    async def setup_hook(self):
        # instant registeration of commands
        if CONFIG.my_guild:
            g = discord.Object(id=CONFIG.my_guild)

            self.tree.add_command(self.admin_group)
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


@client.admin_group.command(description="Create a new group for courses")
@app_commands.describe(name="The group's name")
@admin_perms
async def new_group(interaction: discord.Interaction, name: str):
    status = db.create_group(name=name)
    await interaction.response.send_message(embed=embed_status(status), ephemeral=True)


@client.admin_group.command(description="Create a new course")
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
    status = db.create_course(
        group, name, int(default_channel) if default_channel else None, order
    )
    await interaction.response.send_message(embed=embed_status(status), ephemeral=True)


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


@client.admin_group.command(description="Create a new module")
@app_commands.describe(
    name="The name of the course",
    course="The course that owns this module. Can be left empty if in a default channel",
    order="The ordering of the course inside its group",
)
@admin_perms
async def new_module(
    interaction: discord.Interaction,
    name: str,
    course: int | None = None,
    order: int | None = None,
):
    deduced_course = db.deduce_course(interaction.channel_id)

    if not deduced_course and not course:
        await interaction.response.send_message(
            embed=error_embed(
                msg="You're not in the default channel of any course. Please specify the channel manually."
            )
        )
        return

    status = db.create_module(course or deduced_course["id"], name, order)
    await interaction.response.send_message(embed=embed_status(status), ephemeral=True)


@new_module.autocomplete("course")
async def module_choices(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(
            name=course["name"],
            value=str(course["id"]),
        )
        for course in db.get_all("course")
        if course["name"].lower().startswith(current.lower())
    ]


@client.tree.command(description="Mark a module as done")
@app_commands.describe(module="The module to mark as done")
async def done(interaction: discord.Interaction, module: int):
    status = db.create_entry(interaction.user.id, module)
    await interaction.response.send_message(embed=embed_status(status), ephemeral=True)


@done.autocomplete("module")
async def module_choices(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(
            name=f"{module['courseName']} — {module['name']}"  # not in a default channel
            if "courseName" in module.keys()
            else module["name"],  # in a default channel
            value=str(module["id"]),
        )
        for module in db.get_modules(interaction.user.id, interaction.channel_id)
        if module["name"].lower().startswith(current.lower())
        or module["courseName"].lower().startswith(current.lower())
    ]
