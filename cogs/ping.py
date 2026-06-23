import discord
from discord import app_commands
from discord.ext import commands

class Ping_Command(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='ping', description="Pongs back.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"> **Pong!** \n-#  Latency: {round(self.bot.latency * 1000)}ms")

async def setup(bot: commands.Bot):
    await bot.add_cog(Ping_Command(bot))