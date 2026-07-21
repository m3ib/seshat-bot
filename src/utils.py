"""Helper classes, functions and values."""

import functools
from dataclasses import dataclass
from enum import Enum
from os import path
from typing import Callable

import discord

APP_DIR = path.dirname(path.abspath(__file__))
ROOT_DIR = path.dirname(APP_DIR)


class ExitStatusType(Enum):
    """Represent the type of an ExitStatus of an operation."""

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"

    @property
    def color(self):
        return {
            ExitStatusType.INFO: discord.Color.blue(),
            ExitStatusType.WARNING: discord.Color.orange(),
            ExitStatusType.ERROR: discord.Color.red(),
        }[self]


@dataclass
class ExitStatus:
    """Represent the exit status of an operation."""

    type: ExitStatusType = ExitStatusType.INFO
    title: str = ""
    msg: str = ""
    rowid: int | None = None


def path_from_root(p: str) -> str:
    """Append path to the project root directory."""
    return path.join(ROOT_DIR, p)


def path_from_app(p: str):
    """Append path to the project src directory."""
    return path.join(APP_DIR, p)


def embed_status(status: ExitStatus):
    return discord.Embed(
        title=status.title or status.type.value,
        description=status.msg,
        color=status.type.color,
    )


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
                    embed=embed_status(
                        ExitStatus(
                            type=ExitStatusType.ERROR,
                            msg="You don't have permission to use this command. Please contact an admin.",
                        )
                    ),
                    ephemeral=True,
                )
                return

            await func(*args, **kwargs)

        return wrapper

    return decorator
