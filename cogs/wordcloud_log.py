import discord
from discord import app_commands
from discord.ext import commands
from wordcloud import WordCloud
from io import BytesIO
import os

class WordCloudLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="wordcloud-log", description="Generates a WordCloud from the log history file.")
    async def wordcloud_log(self, interaction: discord.Interaction):
        await interaction.response.defer()

        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(cog_dir)
        log_path = os.path.join(root_dir, "logs", "chat_log.txt")

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                texto = f.read()
        except FileNotFoundError:
            await interaction.followup.send(f"❌ `chat_log.txt` no encontrado en {log_path}")
            return

        if not texto.strip():
            await interaction.followup.send("❌ There's not enough text in the log file to generate the WordCloud.")
            return

        try:
            wc = WordCloud(width=800, height=400, background_color="white").generate(texto)
            buffer = BytesIO()
            wc.to_image().save(buffer, format="PNG")
            buffer.seek(0)

            await interaction.followup.send(
                content="WordCloud generated from log file.",
                file=discord.File(buffer, filename="wordcloud_log.png")
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating WordCloud: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(WordCloudLog(bot))