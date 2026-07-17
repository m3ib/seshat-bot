import discord
from discord import app_commands as apc

from src import db
from src.config import Config
from src.utils import embed_status, error_embed, require_roles


class AdminGroup(apc.Group):
    """Admin privileged commands."""

    admin_roles: list[str] = []

    def __init__(self, client: discord.Client, config: Config) -> None:
        super().__init__(name="admin")
        self.client = client
        self.config = config
        AdminGroup.admin_roles = config.admin_roles

    @apc.command(description="Load data from a JSON string")
    @apc.describe(json="The JSON data")
    @require_roles(lambda: AdminGroup.admin_roles)
    async def from_json(self, interaction: discord.Interaction, json: str):
        status = db.from_json(interaction.guild_id, data=json)
        await interaction.response.send_message(
            embed=embed_status(status), ephemeral=True
        )

