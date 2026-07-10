import discord
from discord import app_commands
from discord.ext import commands
from wordcloud import WordCloud
from io import BytesIO

class WordCloudUser(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="wordcloud-user", 
        description="Generates a WordCloud from all messages sent by a specific user."
    )
    @app_commands.describe(username="The user to generate the WordCloud for")
    async def wordcloud_user(self, interaction: discord.Interaction, username: discord.User):
        await interaction.response.defer()

        if username.bot:
            return await interaction.followup.send("> ❌ You cannot generate a WordCloud for a bot account.")

        try:
            data = getattr(self.bot, 'global_chat_data', [])
            
            mensajes = []
            for msg in data:
                if msg.get("user_id") == username.id:
                    texto_msg = msg.get("content", "").strip()
                    if texto_msg:
                        mensajes.append(texto_msg)
                        
            texto = "\n".join(mensajes)
            
        except Exception as e:
            await interaction.followup.send(f"> ❌ Error reading messages for the user: `{e}`")
            return

        if not texto.strip():
            await interaction.followup.send(f"> ❌ Not enough text from {username.mention} to generate the WordCloud.")
            return

        try:
            wc = WordCloud(width=800, height=400, background_color="white").generate(texto)
            buffer = BytesIO()
            wc.to_image().save(buffer, format="PNG")
            buffer.seek(0)

            await interaction.followup.send(
                content=f"> WordCloud generated for user: {username.mention}",
                file=discord.File(buffer, filename="wordcloud_user.png"),
                allowed_mentions=discord.AllowedMentions.none()
            )
        except Exception as e:
            await interaction.followup.send(f"> ❌ Error generating WordCloud: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(WordCloudUser(bot))
