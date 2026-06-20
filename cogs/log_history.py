import discord
from discord import app_commands
from discord.ext import commands
import random
import os

class LogHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(cog_dir)
        self.log_file = os.path.join(root_dir, "logs", "chat_log.txt")
        
    def _read_log_lines(self):
        """Lee el archivo de log y devuelve las líneas"""
        if not os.path.exists(self.log_file):
            print(f"⚠️ Archivo no encontrado en: {self.log_file}")
            return []
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if lines and "===" in lines[0]:
            lines = lines[1:]
        return lines

    @app_commands.command(
        name="log-history",
        description="Shows up a magical random message!"
    )
    @app_commands.describe(
        value="Message ID to show (leave empty to show a random one!)"
    )
    async def log_history(self, interaction: discord.Interaction, value: int = None):
        lines = self._read_log_lines()
        total_lines = len(lines)
        
        if not lines:
            await interaction.response.send_message(
                "⚠️ There are no registered messages yet, weird.",
                ephemeral=True
            )
            return
        
        if value is not None:
            if value <= 0:
                await interaction.response.send_message("❌ Value must be greater than 0.", ephemeral=True)
                return
            if value > total_lines:
                await interaction.response.send_message(f"❌ Value must be in between 1 and {total_lines}.", ephemeral=True)
                return
            selected_line = lines[value - 1]
        else:
            selected_line = random.choice(lines)
            value = lines.index(selected_line) + 1
        
        await interaction.response.send_message(f"{selected_line}")

async def setup(bot):
    await bot.add_cog(LogHistory(bot))