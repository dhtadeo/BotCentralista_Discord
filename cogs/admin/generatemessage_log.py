import discord
from discord.ext import commands
from cogs.admin._admin_config import ADMIN_PREFIX, get_authorized_users, UNAUTHORIZED_MESSAGE

class GenerateMessageLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.command_prefix = ADMIN_PREFIX
        self.authorized_users = get_authorized_users()

    @commands.command(name="generatemessage", aliases=["genmen", "gmen", "gm"])
    async def generate_message_log(self, ctx):
        if ctx.author.id not in self.authorized_users:
            await ctx.message.delete()
            return await ctx.send(UNAUTHORIZED_MESSAGE, delete_after=5)

        if getattr(self.bot, 'global_markov_model', None) is None:
            return await ctx.send("> ⚠️ Interaction failed, please try again in a few moments.")

        try:
            oracion = None
            for _ in range(50):
                oracion = self.bot.global_markov_model.make_sentence()
                if oracion: break

            if oracion:
                await ctx.send(
                    oracion, 
                    allowed_mentions=discord.AllowedMentions.none()
                )
            else:
                await ctx.send("⚠️ Couldn't generate a coherent message after multiple tries.")
        except Exception as e:
            await ctx.send(f"> ❌ Error generating message: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(GenerateMessageLog(bot))