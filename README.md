# Seshat

> A discord bot to manage user's progress in online courses, like OSSU, the Odin Project, etc...

## Setup

- ```bash
  uv sync # Update the project's environment
  ```
- Create a `.env` file in the root directory, and set its contents to:
  ```
  # Your bot's token, you get it from discord's developer portal
  TOKEN=<paste-here>
  # Optionally, your guild id. This makes the commands reflect instantly, useful while developing
  MY_GUILD=<guild-id>
  ```
- Run using:
  ```bash
  python -m src # while in the project's root
  ```

**See**
- [uv](https://docs.astral.sh/uv/)
- [Discord developer portal](https://discord.com/developers/applications) 
