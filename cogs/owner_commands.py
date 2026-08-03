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
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(cog_dir)
        config_path = os.path.join(root_dir, "config.json")
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("authorized_users", []))
        except (FileNotFoundError, json.JSONDecodeError):
            print("> ⚠️ Missing config parameters.")
            return set()

    @commands.command(name='channelsend', aliases=['cs'])
    async def channel_send(self, ctx, channel_id: str = None, *, message: str = None):
        if ctx.author.id not in self.authorized_users:
            await ctx.message.delete()
            return await ctx.send("> ❌ This command can only be used by a small amount of people. You're not allowed to use this command.", delete_after=5)

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

    @commands.command(name='channelreply', aliases=['cr'])
    async def channel_reply(self, ctx, channel_id: str = None, message_id: str = None, *, message: str = None):
        
        if ctx.author.id not in self.authorized_users:
            await ctx.message.delete()
            return await ctx.send("> ❌ This command can only be used by a small amount of people. You're not allowed to use this command.", delete_after=5)

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

    @commands.command(name='getlogs', aliases=['gl'])
    async def get_logs(self, ctx, file_type: str = None):
        if ctx.author.id not in self.authorized_users:
            return await ctx.send("> ❌ This command can only be used by a small amount of people. You're not allowed to use this command.", delete_after=5)

        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(cog_dir)
        logs_dir = os.path.join(root_dir, "logs")
        
        valid_files = {
            "messages": "messages.json",
            "users": "users.json",
            "servers": "servers.json",
            "channels": "channels.json"
        }
        
        if file_type:
            file_type = file_type.lower()
            if file_type not in valid_files:
                return await ctx.send("> ❌ Invalid file type. Choose from: `messages`, `users`, `servers`, `channels`.", delete_after=10)
            target_files = [valid_files[file_type]]
        else:
            target_files = list(valid_files.values())
        
        files_to_send = []
        for filename in target_files:
            file_path = os.path.join(logs_dir, filename)
            if os.path.exists(file_path):
                files_to_send.append(discord.File(file_path))
                
        if not files_to_send:
            return await ctx.send("> ⚠️ No log files were found for your request in the logs directory.")
            
        msg = await ctx.send("> ⏳ Preparing to send database files...")
        
        try:
            await ctx.send("> 🗄️ Here are the requested database files:", files=files_to_send)
            await msg.delete()
        except discord.HTTPException as e:
            await msg.edit(content=f"> ❌ Failed to send files (they might be too large for Discord limits). Error: `{e}`")
        except Exception as e:
            await msg.edit(content=f"> ❌ An unexpected error occurred: `{e}`")

    @commands.command(name='extractlogs', aliases=['elogs'])
    async def extract_logs_json(self, ctx, limit: int = None, chunk_size: int = 10000):
        if ctx.author.id not in self.authorized_users:
            return await ctx.send("> ❌ This command can only be used by a small amount of people. You're not allowed to use this command.", delete_after=5)

        log_channel_id = 1366171674239832104 
        log_channel = self.bot.get_channel(log_channel_id)

        if not log_channel:
            return await ctx.send("> ❌ Logs channel not found.")

        texto_limite = "the whole history" if limit is None else f"a max of **{limit}** messages"
        msg_estado = await ctx.send(f"> ⏳ Processing **{texto_limite}** messages in batches of **{chunk_size}**... this will take some time.")
        
        ignored_texts = []
        try:
            cog_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(os.path.dirname(cog_dir), "config.json")
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                ignored_texts = data.get("ignored_texts", [])
        except Exception as e:
            print(f"> ⚠️ Error loading config files to reading: {e}")

        def should_ignore(text):
            if not text: return False
            return any(ignored.lower() in text.lower() for ignored in ignored_texts)

        messages_data = []
        users_db = {}
        servers_db = {}
        channels_db = {}
        
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

                server_id = None
                channel_id = None
                message_id = None
                user_id = None
                content = ""
                attachments = []
                
                server_name_fallback = embed.title.replace("📨 Mensaje en ", "") if embed.title else "Servidor Desconocido"

                for field in embed.fields:
                    if field.name == "Enlace":
                        match = re.search(r'channels/(\d+)/(\d+)/(\d+)', field.value)
                        if match:
                            server_id = int(match.group(1))
                            channel_id = int(match.group(2))
                            message_id = int(match.group(3))
                    elif field.name == "Canal":
                        match = re.search(r'<#(\d+)>', field.value)
                        if match and not channel_id: channel_id = int(match.group(1))
                    elif field.name == "Autor":
                        match = re.search(r'\(ID:\s*(\d+)\)', field.value)
                        if match: user_id = int(match.group(1))
                    elif field.name == "Contenido":
                        if field.value != "*Sin contenido de texto*":
                            content = field.value
                    elif field.name == "Archivos adjuntos":
                        urls = re.findall(r'\((https?://[^\)]+)\)', field.value)
                        attachments = urls

                if should_ignore(content):
                    continue

                if not message_id or not user_id or not channel_id or not server_id:
                    continue

                guild = self.bot.get_guild(server_id)
                if guild:
                    servers_db[server_id] = {
                        "server_id": server_id,
                        "name": guild.name,
                        "icon": guild.icon.url if guild.icon else None,
                        "timestamp": guild.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                else:
                    servers_db[server_id] = {
                        "server_id": server_id,
                        "name": server_name_fallback,
                        "icon": None,
                        "timestamp": None
                    }

                channel = self.bot.get_channel(channel_id)
                if channel:
                    channels_db[channel_id] = {
                        "channel_id": channel_id,
                        "server_id": server_id,
                        "name": channel.name,
                        "type": str(channel.type),
                        "timestamp": channel.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                else:
                    if channel_id not in channels_db:
                        channels_db[channel_id] = {
                            "channel_id": channel_id,
                            "server_id": server_id,
                            "name": f"Canal Borrado ({channel_id})",
                            "type": None,
                            "timestamp": None
                        }

                user = self.bot.get_user(user_id)
                if user:
                    users_db[user_id] = {
                        "user_id": user_id,
                        "name": user.display_name,
                        "username": user.name,
                        "icon": user.avatar.url if user.avatar else user.default_avatar.url,
                        "is_bot": user.bot,
                        "timestamp": user.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                else:
                    if user_id not in users_db:
                        users_db[user_id] = {
                            "user_id": user_id,
                            "name": "Usuario Desconocido",
                            "username": "desconocido",
                            "icon": None,
                            "is_bot": False,
                            "timestamp": None
                        }

                messages_data.append({
                    "message_id": message_id,
                    "content": content,
                    "attachments": attachments,
                    "user_id": user_id,
                    "channel_id": channel_id,
                    "server_id": server_id,
                    "created_at": timestamp_str
                })

                total_processed += 1

                if len(messages_data) >= chunk_size:
                    file_path = f"messages_pt{part_number}.json"
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(messages_data, f, ensure_ascii=False, indent=4)

                    await ctx.send(f"> 📦 Sending messages part {part_number} ({len(messages_data)} messages)...", file=discord.File(file_path))
                    os.remove(file_path)

                    messages_data.clear()
                    part_number += 1

            if messages_data:
                file_path = f"messages_pt{part_number}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(messages_data, f, ensure_ascii=False, indent=4)

                await ctx.send(f"> 📦 Sending messages part {part_number} and final ({len(messages_data)} messages)...", file=discord.File(file_path))
                os.remove(file_path)
                
            dbs = {
                "users.json": users_db,
                "servers.json": servers_db,
                "channels.json": channels_db
            }
            
            files_to_send = []
            for filename, data_dict in dbs.items():
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data_dict, f, ensure_ascii=False, indent=4)
                files_to_send.append(discord.File(filename))
                
            if files_to_send:
                await ctx.send("> 🗄️ Sending relational databases...", files=files_to_send)
                for f in files_to_send:
                    os.remove(f.filename)

            await msg_estado.edit(content=f"> ✅ Extraction complete. {total_processed} messages processed and relations mapped successfully.")

        except Exception as e:
            await ctx.send(f"> ❌ Error during the extraction: `{e}`")

async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))
