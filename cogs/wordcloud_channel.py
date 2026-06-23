import discord
from discord import app_commands
from discord.ext import commands
from wordcloud import WordCloud
from io import BytesIO

class WordCloudChannel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="wordcloud-channel", description="Generates a WordCloud from a specified text channel.")
    @app_commands.describe(
        channel="The text channel to read messages from"
    )
    async def wordcloud_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        await interaction.response.defer()

        try:
            mensajes = []
            async for msg in channel.history(limit=2000):
                if not msg.author.bot:
                    mensajes.append(msg.content)
            texto = "\n".join(mensajes)
        except Exception as e:
            await interaction.followup.send(f"> ❌ Error reading messages from the channel: `{e}`")
            return

        if not texto.strip():
            await interaction.followup.send("> ❌ Not enough text in the channel to generate the WordCloud.")
            return

        try:
            wc = WordCloud(width=800, height=400, background_color="white").generate(texto)
            buffer = BytesIO()
            wc.to_image().save(buffer, format="PNG")
            buffer.seek(0)

            await interaction.followup.send(
                content=f"> WordCloud generated from channel: {channel.mention}",
                file=discord.File(buffer, filename="wordcloud_channel.png")
            )
        except Exception as e:
            await interaction.followup.send(f"> ❌ Error generating WordCloud: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(WordCloudChannel(bot))
