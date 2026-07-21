import functools
import sqlite3

import discord
from discord import app_commands as apc

from src import db
from src.config import Config
from src.utils import embed_status, error_embed


class ShowGroup(apc.Group):
    """Group for commands that show progress."""

    def __init__(self, client: discord.Client, config: Config) -> None:
        super().__init__(name="show")
        self.client = client
        self.config = config

    @apc.command(name="course", description="Show current progress in a certain course")
    @apc.describe(course="The course to show")
    async def show_course(self, interaction: discord.Interaction, course: str):
        con = db.get_db()
        course_row = con.execute(
            "SELECT * FROM course WHERE id = ?", (course,)
        ).fetchone()

        status = db.course_progress(interaction.user.id, course)
        await interaction.response.send_message(embed=embed_status(status))

    @show_course.autocomplete("course")
    async def show_course_autocomplete_course(
        self, interaction: discord.Interaction, current: str
    ) -> list[apc.Choice[str]]:
        return [
            apc.Choice(
                name=course["name"],
                value=str(course["id"]),
            )
            for course in db.get_all("course")
            if course["name"].lower().startswith(current.lower())
        ][:25]
