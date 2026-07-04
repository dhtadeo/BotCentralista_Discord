import discord
from discord import app_commands
from discord.ext import commands
import markovify

class GenerateMessageChannel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="generate-message-channel", 
        description="Generates a coherent message based on messages sent in the selected channel."
    )
    @app_commands.describe(channel="The text channel to fetch messages from")
    async def generate_message_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        data = getattr(self.bot, 'global_chat_data', [])
        
        if not data:
            return await interaction.followup.send("> ⚠️ Failed to generate a message.")

        try:
            mensajes = []
            for msg in data:
                if msg.get("channel_id") == channel.id:
                    texto_msg = msg.get("content", "").strip()
                    adjuntos = msg.get("attachments", [])
                    
                    if texto_msg or adjuntos:
                        linea = texto_msg
                        if adjuntos:
                            linea += " " + " ".join(adjuntos)
                        mensajes.append(linea.strip())
                        
            texto = "\n".join(mensajes)
                
            if not texto.strip() or len(texto.splitlines()) < 5:
                return await interaction.followup.send(f"> ❌ Not enough messages stored for {channel.mention} yet. Lock in! ")

            modelo = markovify.NewlineText(texto, well_formed=False)
            
            oracion = None
            for _ in range(50):
                oracion = modelo.make_sentence()
                if oracion: break

            if oracion:
                await interaction.followup.send(
                    oracion,
                    allowed_mentions=discord.AllowedMentions.none()
                )
            else:
                await interaction.followup.send("> ⚠️ Couldn't generate a message after many tries...")

        except Exception as e:
            await interaction.followup.send(f"> ❌ Error: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(GenerateMessageChannel(bot))