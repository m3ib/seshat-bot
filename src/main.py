"""the core logic of the app."""

import discord


class MyClient(discord.Client):
    async def on_read(self):
        print(f"Logged on as {self.user}")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        print(f"Message from {message.author} in {message.guild}: {message.content}")


intents = discord.Intents.default()
intents.message_content = True
