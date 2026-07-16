import discord
from discord import app_commands as apc

from src import db
from src.config import Config
from src.utils import embed_status, error_embed, require_roles


class AdminGroup(apc.Group):
    """Admin privileged commands."""

    admin_roles = []

    def __init__(self, client: discord.Client, config: Config) -> None:
        super().__init__(name="admin")
        self.client = client
        self.config = config
        admin_roles = config.admin_roles

