import discord
from discord.ext import commands
import json
import os
import re

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

    @commands.command(name='extractlogs_json', aliases=['elogsj'])
    async def extract_logs_json(self, ctx, limit: int = None, chunk_size: int = 10000):
        if ctx.author.id not in self.authorized_users:
            return await ctx.send("❌ This command can only be used by a small amount of people. You're not allowed to use this command.", delete_after=5)

        log_channel_id = 1366171674239832104 
        log_channel = self.bot.get_channel(log_channel_id)

        if not log_channel:
            return await ctx.send("❌ Logs channel not found.")

        texto_limite = "the whole history" if limit is None else f"a max of {limit} messages"
        msg_estado = await ctx.send(f"⏳ Processing {texto_limite} in batches of {chunk_size}... this will take some time.")
        
        ignored_texts = []
        try:
            cog_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(os.path.dirname(cog_dir), "config.json")
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                ignored_texts = data.get("ignored_texts", [])
        except Exception as e:
            print(f"⚠️ Error loading config files to reading: {e}")

        def should_ignore(text):
            if not text: return False
            return any(ignored.lower() in text.lower() for ignored in ignored_texts)

        extracted_data = []
        part_number = 1
        total_processed = 0

        try:
            async for message in log_channel.history(limit=limit, oldest_first=True):
                if not message.embeds:
                    continue
                
                embed = message.embeds[0]
                
                if embed.title == "📨 Mensaje Directo":
                    continue

                if embed.timestamp:
                    timestamp_str = embed.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    timestamp_str = message.created_at.strftime('%Y-%m-%d %H:%M:%S')

                data_entry = {
                    "server_id": None,
                    "channel_id": None,
                    "user_id": None,
                    "timestamp": timestamp_str,
                    "content": "",
                    "attachments": []
                }

                for field in embed.fields:
                    if field.name == "Enlace":
                        match = re.search(r'channels/(\d+)/', field.value)
                        if match: data_entry["server_id"] = int(match.group(1))
                    elif field.name == "Canal":
                        match = re.search(r'<#(\d+)>', field.value)
                        if match: data_entry["channel_id"] = int(match.group(1))
                    elif field.name == "Autor":
                        match = re.search(r'\(ID:\s*(\d+)\)', field.value)
                        if match: data_entry["user_id"] = int(match.group(1))
                    elif field.name == "Contenido":
                        if field.value != "*Sin contenido de texto*":
                            data_entry["content"] = field.value
                    elif field.name == "Archivos adjuntos":
                        urls = re.findall(r'\((https?://[^\)]+)\)', field.value)
                        data_entry["attachments"] = urls

                if should_ignore(data_entry["content"]):
                    continue

                extracted_data.append(data_entry)
                total_processed += 1

                if len(extracted_data) >= chunk_size:
                    file_path = f"logs_estructurados_pt{part_number}.json"
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(extracted_data, f, ensure_ascii=False, indent=4)

                    await ctx.send(f"📦 Sending part {part_number} ({len(extracted_data)} messages)...", file=discord.File(file_path))
                    os.remove(file_path)

                    extracted_data.clear()
                    part_number += 1

            if extracted_data:
                file_path = f"logs_estructurados_pt{part_number}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(extracted_data, f, ensure_ascii=False, indent=4)

                await ctx.send(f"📦 Sending part {part_number} final ({len(extracted_data)} messages)...", file=discord.File(file_path))
                os.remove(file_path)

            await msg_estado.edit(content=f"✅ Extraction complete. {total_processed} were sent and extracted in total.")

        except Exception as e:
            await ctx.send(f"❌ Error during the extraction: {e}")

async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))