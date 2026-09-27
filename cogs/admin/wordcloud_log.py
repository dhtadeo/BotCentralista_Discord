import discord
from discord.ext import commands
from wordcloud import WordCloud
from io import BytesIO
from cogs.admin._admin_config import ADMIN_PREFIX, get_authorized_users, UNAUTHORIZED_MESSAGE

class WordCloudLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.command_prefix = ADMIN_PREFIX
        self.authorized_users = get_authorized_users()

    @commands.command(name="wordcloud", aliases=["wc"])
    async def wordcloud_log(self, ctx):
        if ctx.author.id not in self.authorized_users:
            await ctx.message.delete()
            return await ctx.send(UNAUTHORIZED_MESSAGE, delete_after=5)

        msg = await ctx.send("> ⏳ Generating WordCloud...")

        try:
            data = getattr(self.bot, 'global_chat_data', [])
            messages = [m.get("content", "").strip() for m in data if m.get("content")]
            text = "\n".join(messages)
        except Exception as e:
            return await msg.edit(content=f"> ❌ Error reading log data: `{e}`")

        if not text.strip():
            return await msg.edit(content="> ❌ There's not enough text in the logs to generate the WordCloud.")

        try:
            wc = WordCloud(width=800, height=400, background_color="white").generate(text)
            buffer = BytesIO()
            wc.to_image().save(buffer, format="PNG")
            buffer.seek(0)

            await ctx.send(
                content="> WordCloud generated from log files.",
                file=discord.File(buffer, filename="wordcloud_log.png")
            )
            await msg.delete()
        except Exception as e:
            await msg.edit(content=f"> ❌ Error generating WordCloud: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(WordCloudLog(bot))