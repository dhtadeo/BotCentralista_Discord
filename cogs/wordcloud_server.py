import discord
from discord import app_commands
from discord.ext import commands
from wordcloud import WordCloud
from io import BytesIO

class WordCloudServer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="wordcloud-server", 
        description="Generates a WordCloud from all messages sent in this server."
    )
    async def wordcloud_server(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not interaction.guild:
            return await interaction.followup.send("> ❌ This command can only be used inside a server.")

        try:
            data = getattr(self.bot, 'global_chat_data', [])
            
            mensajes = []
            for msg in data:
                if msg.get("server_id") == interaction.guild.id:
                    if msg.get("user_id") == self.bot.user.id:
                        continue
                    
                    texto_msg = msg.get("content", "").strip()
                    if texto_msg:
                        mensajes.append(texto_msg)
                        
            texto = "\n".join(mensajes)
            
        except Exception as e:
            await interaction.followup.send(f"> ❌ Error reading messages from the server: `{e}`")
            return

        if not texto.strip():
            await interaction.followup.send("> ❌ Not enough text in this server to generate the WordCloud.")
            return

        try:
            wc = WordCloud(width=800, height=400, background_color="white").generate(texto)
            buffer = BytesIO()
            wc.to_image().save(buffer, format="PNG")
            buffer.seek(0)

            await interaction.followup.send(
                content=f"> WordCloud generated for server: **{interaction.guild.name}**",
                file=discord.File(buffer, filename="wordcloud_server.png")
            )
        except Exception as e:
            await interaction.followup.send(f"> ❌ Error generating WordCloud: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(WordCloudServer(bot))
