"""Helper classes, functions and values."""

import functools
from dataclasses import dataclass
from enum import Enum
from os import path
from typing import Callable

import discord

APP_DIR = path.dirname(path.abspath(__file__))
ROOT_DIR = path.dirname(APP_DIR)


class StatusType(Enum):
    INFO = 1
    WARNING = 2
    ERROR = 3


@dataclass
class Status:
    """Represent the exit status of a db operation."""

    type: StatusType = StatusType.INFO
    title: str = ""
    msg: str = ""
    rowid: int | None = None


def path_from_root(p: str) -> str:
    """Append path to the project root directory."""
    return path.join(ROOT_DIR, p)


def path_from_app(p: str):
    """Append path to the project src directory."""
    return path.join(APP_DIR, p)


def info_embed(msg: str, title: str = "") -> discord.Embed:
    """Create an embed to show an informational message"""
    return discord.Embed(
        title=title or "Info", description=msg, color=discord.Color.blue()
    )


def error_embed(msg: str, title: str = "") -> discord.Embed:
    """Create an embed to show an error message"""
    return discord.Embed(
        title=title or "Error", description=msg, color=discord.Color.red()
    )


def embed_status(status: Status):
    if status.type == StatusType.ERROR:
        return error_embed(msg=status.msg, title=status.title)

    return info_embed(msg=status.msg, title=status.title)


def require_roles(roles: list[str] | Callable) -> Callable:
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # find the interaction object
            interaction = kwargs.get("interaction")
            if interaction is None:
                for a in args:
                    if isinstance(a, discord.Interaction):
                        interaction = a
                        break

            user_roles: list[str] = [str(r).lower() for r in interaction.user.roles]
            required_roles = roles() if callable(roles) else roles

            if not any(
                [
                    required_role.lower() in user_roles
                    for required_role in required_roles
                ]
            ):
                await interaction.response.send_message(
                    embed=error_embed(
                        "You don't have permission to use this command. Please contact an admin."
                    ),
                    ephemeral=True,
                )
                return

            await func(*args, **kwargs)

        return wrapper

    return decorator
