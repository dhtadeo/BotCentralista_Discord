import discord
from discord import app_commands
from discord.ext import commands
import markovify
import os

class GenerateMessageChannel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Optimized version
    @app_commands.command(
        name="gen-message-channel", 
        description="Generates a message based on messages sent in the selected channel (Fast)."
    )
    @app_commands.describe(channel="The text channel to fetch messages from")
    async def generate_message_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(cog_dir)
        
        server_id = str(interaction.guild_id)
        channel_id = str(channel.id)
        log_path = os.path.join(root_dir, "logs", "server", server_id, f"{channel_id}.txt")

        try:
            if not os.path.exists(log_path):
                await interaction.followup.send(f"❌ No message logs found for {channel.mention} yet. Use the `-legacy` version!")
                return

            with open(log_path, "r", encoding="utf-8") as f:
                texto = f.read()
                
            if not texto.strip() or len(texto.splitlines()) < 5:
                await interaction.followup.send("❌ Not enough messages yet. Try the `-legacy` version while more messages gets sent here.")
                return

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

    # Legacy version
    @app_commands.command(
        name="gen-message-channel-legacy", 
        description="Generates a message based on messages sent in the selected channel (Slow but complete)."
    )
    @app_commands.describe(channel="The text channel to fetch messages from")
    async def generate_message_channel_legacy(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        try:
            mensajes = []
            async for msg in channel.history(limit=2000):
                if not msg.author.bot and msg.content.strip():
                    mensajes.append(msg.content)
            
            if not mensajes:
                await interaction.followup.send("❌ Could not find any messages in the history of that channel.")
                return

            texto = "\n".join(mensajes)
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
            await interaction.followup.send(f"❌ Legacy Error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(GenerateMessageChannel(bot))