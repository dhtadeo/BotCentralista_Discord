import discord
from discord import app_commands
from discord.ext import commands
import markovify
import os

class GenerateMessageLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(cog_dir)
        self.log_path = os.path.join(self.root_dir, "logs", "chat_log.txt")

    @app_commands.command(name="gen-message-log", description="Generates a message using data from the chat log file.")
    async def generate_message_log(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                texto = f.read()
        except FileNotFoundError:
            await interaction.followup.send(f"❌ `chat_log.txt` not found. Buscando en: {self.log_path}")
            return

        if not texto.strip():
            await interaction.followup.send("❌ Not enough text in the log to generate a message.")
            return

        try:
            modelo = markovify.NewlineText(texto, well_formed=False)
            oracion = None
            for _ in range(50):
                oracion = modelo.make_sentence()
                if oracion:
                    break

            if oracion:
                # Aplicamos AllowedMentions aquí también por pura seguridad
                await interaction.followup.send(
                    f"{oracion}",
                    allowed_mentions=discord.AllowedMentions.none()
                )
            else:
                await interaction.followup.send("⚠️ Couldn't generate a coherent message after multiple tries.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating message: {e}")

    # --- FUNCIÓN: RESPONDER A MENCIONES Y RESPUESTAS ---
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        bot_mentioned = self.bot.user in message.mentions

        is_reply_to_bot = False
        if message.reference and message.reference.message_id:
            try:
                cached_msg = message.reference.cached_message
                if cached_msg and cached_msg.author == self.bot.user:
                    is_reply_to_bot = True
                elif not cached_msg:
                    replied_msg = await message.channel.fetch_message(message.reference.message_id)
                    if replied_msg.author == self.bot.user:
                        is_reply_to_bot = True
            except Exception:
                pass 

        if not (bot_mentioned or is_reply_to_bot):
            return

        async with message.channel.typing():
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    texto = f.read()
            except FileNotFoundError:
                return 

            if not texto.strip() or len(texto.splitlines()) < 5:
                return 

            try:
                modelo = markovify.NewlineText(texto, well_formed=False)
                oracion = None
                for _ in range(50):
                    oracion = modelo.make_sentence()
                    if oracion:
                        break

                if oracion:
                    mentions_config = discord.AllowedMentions(
                        everyone=False, 
                        users=False, 
                        roles=False, 
                        replied_user=False
                    )
                    
                    await message.reply(oracion, allowed_mentions=mentions_config)
            except Exception as e:
                print(f"❌ Error al intentar auto-responder: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(GenerateMessageLog(bot))