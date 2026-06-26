"""Functions and values used throughout the entire app."""

from os import path
from pydoc import doc

import discord

APP_DIR = path.dirname(path.abspath(__file__))
ROOT_DIR = path.dirname(APP_DIR)


def path_from_root(p: str) -> str:
    """Append path to the project root directory."""
    return path.join(ROOT_DIR, p)


def path_from_app(p: str):
    """Append path to the project src directory."""
    return path.join(APP_DIR, p)


def info_embed(desc: str) -> discord.Embed:
    """Create an embed to show an informational message"""
    return discord.Embed(title="Info", description=desc, color=discord.Color.blue())


def error_embed(desc: str) -> discord.Embed:
    """Create an embed to show an error message"""
    return discord.Embed(title="Error", description=desc, color=discord.Color.red())
