"""The entry point to the app."""

import os

from dotenv import load_dotenv

from .db import init_db
from .main import MyClient, intents

load_dotenv()

if __name__ == "__main__":
    init_db()

    client = MyClient(intents=intents)
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        client.run(TOKEN)
    else:
        raise RuntimeError("can't run without a token.")
