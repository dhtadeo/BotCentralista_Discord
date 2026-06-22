import discord
from discord import app_commands
from discord.ext import commands
import markovify
import os
import json

class GenerateMessageChannel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="gen-message-channel", 
        description="Generates a message based on messages sent in the selected channel."
    )
    @app_commands.describe(channel="The text channel to fetch messages from")
    async def generate_message_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(cog_dir)
        log_path = os.path.join(root_dir, "logs", "chat_log.json")

        try:
            if not os.path.exists(log_path):
                return await interaction.followup.send("❌ `chat_log.json` not found yet.")

            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            mensajes = [msg["content"] for msg in data if msg.get("channel_id") == channel.id and msg.get("content")]
            texto = "\n".join(mensajes)
                
            if not texto.strip() or len(texto.splitlines()) < 5:
                return await interaction.followup.send(f"❌ Not enough messages logged for {channel.mention} yet.")

            modelo = markovify.NewlineText(texto, well_formed=False)
            
            oracion = None
            for _ in range(50):
                oracion = modelo.make_sentence()
                if oracion: break

            if oracion:
                await interaction.followup.send(f"{oracion}")
            else:
                await interaction.followup.send("⚠️ Couldn't generate a message after many tries...")

        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(GenerateMessageChannel(bot))