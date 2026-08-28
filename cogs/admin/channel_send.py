import discord
from discord.ext import commands
from cogs.admin._admin_config import ADMIN_PREFIX, get_authorized_users, UNAUTHORIZED_MESSAGE

class ChannelSend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_prefix = ADMIN_PREFIX
        self.authorized_users = get_authorized_users()

    @commands.command(name='channelsend', aliases=['cs'])
    async def channel_send(self, ctx, channel_id: str = None, *, message: str = None):
        if ctx.author.id not in self.authorized_users:
            await ctx.message.delete()
            return await ctx.send(UNAUTHORIZED_MESSAGE, delete_after=5)

        if not channel_id or not message:
            embed = discord.Embed(
                title="Correct usage",
                description=(
                    f"**{self.command_prefix}.channelsend** `<Channel_ID>` `<message>`\n"
                    f"**Aliases:** `{self.command_prefix}.cs`\n"
                    f"**Example:**\n"
                    f"`{self.command_prefix}.cs 123456789012345678 Hi!`"
                ),
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, delete_after=15)

        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return await ctx.send("> ❌ Channel not found.", delete_after=5)
                
            await channel.send(message)
            await ctx.send(f"> ✅ Message sent to {channel.mention}", delete_after=5)
            
        except ValueError:
            await ctx.send("> ❌ Channel ID must be a number.", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}", delete_after=10)

async def setup(bot):
    await bot.add_cog(ChannelSend(bot))