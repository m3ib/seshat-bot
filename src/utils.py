"""Helper classes, functions and values."""

from dataclasses import dataclass
from enum import Enum
from os import path
from pydoc import doc

import discord

APP_DIR = path.dirname(path.abspath(__file__))
ROOT_DIR = path.dirname(APP_DIR)


class StatusType(Enum):
    INFO = 1
    ERROR = 2


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
