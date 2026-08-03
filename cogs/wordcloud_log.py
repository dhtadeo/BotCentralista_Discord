import discord
from discord import app_commands
from discord.ext import commands
from wordcloud import WordCloud
from io import BytesIO

class WordCloudLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="wordcloud-log", description="Generates a WordCloud using logs and some magic.")
    async def wordcloud_log(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            data = getattr(self.bot, 'global_chat_data', [])
            mensajes = [msg.get("content", "").strip() for msg in data if msg.get("content")]
            texto = "\n".join(mensajes)
        except Exception as e:
            return await interaction.followup.send(f"> ❌ Error reading log data: `{e}`")

        if not texto.strip():
            return await interaction.followup.send("> ❌ There's not enough text in the logs to generate the WordCloud.")

        try:
            wc = WordCloud(width=800, height=400, background_color="white").generate(texto)
            buffer = BytesIO()
            wc.to_image().save(buffer, format="PNG")
            buffer.seek(0)

            await interaction.followup.send(
                content="> WordCloud generated from log files.",
                file=discord.File(buffer, filename="wordcloud_log.png")
            )
        except Exception as e:
            await interaction.followup.send(f"> ❌ Error generating WordCloud: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(WordCloudLog(bot))
