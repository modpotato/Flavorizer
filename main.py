import os
import discord
from discord import app_commands
from commands import flavorize
from commands import split_audio

class InterpolateClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync commands to a specific server
        guild = discord.Object(id=1158539552911274014)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

client = InterpolateClient()

client.tree.add_command(flavorize.flavorize)
client.tree.add_command(split_audio.split_audio)

with open('token', 'r') as file:
    token = file.read().strip()
client.run(token)