"""Configuration data."""

from dataclasses import dataclass, field
from os import getenv

from dotenv import load_dotenv

from .utils import path_from_root

load_dotenv()


@dataclass
class Config:
    token: str | None = getenv("TOKEN")
    db: str = path_from_root("instance/bot.db")
    my_guild: str | None = getenv("MY_GUILD")
    admin_roles: list[str] = field(
        default_factory=lambda: ["owner", "admin", "mod"]
    )  # case insensitive
