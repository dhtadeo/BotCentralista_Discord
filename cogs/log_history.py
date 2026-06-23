import discord
from discord import app_commands
from discord.ext import commands
import random
import os
import json

class LogHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(cog_dir)
        self.log_file = os.path.join(root_dir, "logs", "chat_log.json")

    @app_commands.command(
        name="log-history",
        description="Shows up a magical random message stored in the ancient vaults!"
    )
    @app_commands.describe(
        value="Message ID to show (leave empty to show a random one)"
    )
    async def log_history(self, interaction: discord.Interaction, value: int = None):
        if not os.path.exists(self.log_file):
            return await interaction.response.send_message("> ⚠️ Log files not found on the system. This is not your fault, it's the developer's fault!", ephemeral=True)
            
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return await interaction.response.send_message(f"> ❌ Error reading log files: `{e}`", ephemeral=True)
            
        total_lines = len(data)
        
        if total_lines == 0:
            return await interaction.response.send_message("> ⚠️ Surprisingly, there are no logged message yet...", ephemeral=True)
        
        if value is not None:
            if value <= 0 or value > total_lines:
                return await interaction.response.send_message(f"> ❌ Value must be in between **1** and **{total_lines}**.", ephemeral=True)
            selected_msg = data[value - 1]
        else:
            selected_msg = random.choice(data)
            value = data.index(selected_msg) + 1
        
        adjuntos_lista = selected_msg.get('attachments', [])
        adjuntos = "\n " + "\n ".join(adjuntos_lista) if adjuntos_lista else ""
        
        content = selected_msg.get('content', '*Sin contenido de texto*')

        formato = (
            f"{content}"
            f"{adjuntos}"
        )
        
        await interaction.response.send_message(formato)

async def setup(bot):
    await bot.add_cog(LogHistory(bot))