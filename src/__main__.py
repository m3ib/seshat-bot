"""The entry point to the app."""

from .db import init_db
from .main import CONFIG, client

if __name__ == "__main__":
    init_db(CONFIG)

    if CONFIG.token:
        client.run(CONFIG.token)
    else:
        raise RuntimeError("can't run without a token.")
