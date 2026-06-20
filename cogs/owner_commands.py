import discord
from discord.ext import commands
import json
import os

class OwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_prefix = 'bc'
        self.authorized_users = self._load_authorized_users()

    def _load_authorized_users(self):
        """Lee el archivo config.json y devuelve un set de IDs"""
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(cog_dir)
        config_path = os.path.join(root_dir, "config.json")
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("authorized_users", []))
        except (FileNotFoundError, json.JSONDecodeError):
            print("⚠️ Missing config parameters.")
            return set()

    # --- ENVIAR A CANAL ---
    @commands.command(name='channelsend', aliases=['cs'])
    async def channel_send(self, ctx, channel_id: str = None, *, message: str = None):
        if ctx.author.id not in self.authorized_users:
            await ctx.message.delete()
            return await ctx.send("❌ This command can only be used by a small amount of people. You're not allowed to use this command.", delete_after=5)

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
                return await ctx.send("❌ Channel not found.", delete_after=5)
                
            await channel.send(message)
            await ctx.send(f"✅ Message sent to {channel.mention}", delete_after=5)
            
        except ValueError:
            await ctx.send("❌ Channel ID must be a number.", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}", delete_after=10)


    # --- RESPONDER A MENSAJE ---
    @commands.command(name='channelreply', aliases=['cr'])
    async def channel_reply(self, ctx, channel_id: str = None, message_id: str = None, *, message: str = None):
        
        if ctx.author.id not in self.authorized_users:
            await ctx.message.delete()
            return await ctx.send("❌ Unauthorized access.", delete_after=5)

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
                return await ctx.send("❌ Channel not found.", delete_after=5)
            
            try:
                target_message = await channel.fetch_message(int(message_id))
            except discord.NotFound:
                return await ctx.send("❌ Message not found in that channel.", delete_after=5)
                
            await channel.send(message, reference=target_message)
            await ctx.send(f"✅ Replied successfully in {channel.mention}", delete_after=5)
            
        except ValueError:
            await ctx.send("❌ Channel ID and Message ID must be numbers.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ Missing permissions to read history or send messages in that channel.", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}", delete_after=10)

async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))