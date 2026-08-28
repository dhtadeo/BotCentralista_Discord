import discord
from discord.ext import commands
from cogs.admin._admin_config import ADMIN_PREFIX, get_authorized_users, UNAUTHORIZED_MESSAGE

class ChannelReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_prefix = ADMIN_PREFIX
        self.authorized_users = get_authorized_users()

    @commands.command(name='channelreply', aliases=['cr'])
    async def channel_reply(self, ctx, channel_id: str = None, message_id: str = None, *, message: str = None):
        
        if ctx.author.id not in self.authorized_users:
            await ctx.message.delete()
            return await ctx.send(UNAUTHORIZED_MESSAGE, delete_after=5)

        if not channel_id or not message_id or not message:
            embed = discord.Embed(
                title="Correct usage",
                description=(
                    f"**{self.command_prefix}.channelreply** `<Channel_ID>` `<Message_ID>` `<message>`\n"
                    f"**Aliases:** `{self.command_prefix}.cr`\n"
                    f"**Example:**\n"
                    f"`{self.command_prefix}.cr 123456789 987654321 That's a great idea!`"
                ),
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed, delete_after=15)

        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return await ctx.send("> ❌ Channel not found.", delete_after=5)
            
            try:
                target_message = await channel.fetch_message(int(message_id))
            except discord.NotFound:
                return await ctx.send("> ❌ Message not found in that channel.", delete_after=5)
                
            await channel.send(message, reference=target_message)
            await ctx.send(f"> ✅ Replied successfully in {channel.mention}", delete_after=5)
            
        except ValueError:
            await ctx.send("> ❌ Channel ID and Message ID must be numbers.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("> ❌ Missing permissions to read history or send messages in that channel.", delete_after=5)
        except Exception as e:
            await ctx.send(f"> ❌ Error: `{str(e)}`", delete_after=10)

async def setup(bot):
    await bot.add_cog(ChannelReply(bot))