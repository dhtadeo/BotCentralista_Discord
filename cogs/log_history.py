import discord
from discord import app_commands
from discord.ext import commands
import random
import os
import json
import sqlite3

class LogHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(cog_dir)
        self.db_path = os.path.join(root_dir, "logs", "bc_logs.db")
        self.config_path = os.path.join(root_dir, "config.json")

    def _get_blacklist_channels(self):
        try:
            if not os.path.exists(self.config_path):
                return []
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                raw_blacklist = data.get("blacklist_channels", [])
                return [int(ch) for ch in raw_blacklist if str(ch).isdigit()]
        except Exception as e:
            print(f"[LogHistory] ⚠️ Error loading blacklist_channels from config.json: {e}")
            return []

    @app_commands.command(
        name="log-history",
        description="Shows up a magical random message stored in the ancient vaults!"
    )
    @app_commands.describe(
        value="Message ID to show (leave empty to show a random one)"
    )
    async def log_history(self, interaction: discord.Interaction, value: int = None):
        if not os.path.exists(self.db_path):
            return await interaction.response.send_message("> ⚠️ Log database not found on the system.", ephemeral=True)
            
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_lines = cursor.fetchone()[0]
            
            if total_lines == 0:
                conn.close()
                return await interaction.response.send_message("> ⚠️ Surprisingly, there are no logged messages yet...", ephemeral=True)
            
            blacklist = self._get_blacklist_channels()

            if value is not None:
                if value <= 0 or value > total_lines:
                    conn.close()
                    return await interaction.response.send_message(f"> ❌ Value must be in between **1** and **{total_lines}**.", ephemeral=True)
                
                offset = value - 1
                cursor.execute("SELECT content, attachments, channel_id FROM messages LIMIT 1 OFFSET ?", (offset,))
                row = cursor.fetchone()
                conn.close()

                if not row:
                    return await interaction.response.send_message("> ❌ Message not found.", ephemeral=True)

                content_raw, attachments_raw, channel_id = row[0], row[1], row[2]

                if channel_id and int(channel_id) in blacklist:
                    return await interaction.response.send_message("> 🔒 Locked message. Try with a different `value`.", ephemeral=True)

            else:
                if blacklist:
                    placeholders = ','.join('?' * len(blacklist))
                    query = f"""
                        WITH numbered AS (
                            SELECT ROW_NUMBER() OVER (ORDER BY rowid) AS row_num, content, attachments, channel_id 
                            FROM messages
                        ) 
                        SELECT row_num, content, attachments, channel_id 
                        FROM numbered 
                        WHERE channel_id NOT IN ({placeholders}) 
                        ORDER BY RANDOM() 
                        LIMIT 1
                    """
                    cursor.execute(query, tuple(blacklist))
                else:
                    query = """
                        WITH numbered AS (
                            SELECT ROW_NUMBER() OVER (ORDER BY rowid) AS row_num, content, attachments, channel_id 
                            FROM messages
                        ) 
                        SELECT row_num, content, attachments, channel_id 
                        FROM numbered 
                        ORDER BY RANDOM() 
                        LIMIT 1
                    """
                    cursor.execute(query)

                row = cursor.fetchone()
                conn.close()

                if not row:
                    return await interaction.response.send_message("> ⚠️ No available messages to display...", ephemeral=True)

                value, content_raw, attachments_raw, channel_id = row[0], row[1], row[2], row[3]

            attachments_lista = []
            if attachments_raw:
                try:
                    attachments_lista = json.loads(attachments_raw)
                except Exception:
                    attachments_lista = []
                    
            content_text = content_raw.strip() if content_raw else ""

            if content_text and attachments_lista:
                formato = f"{content_text}\n " + "\n ".join(attachments_lista)
            elif content_text:
                formato = content_text
            elif attachments_lista:
                formato = "\n ".join(attachments_lista)
            else:
                formato = "*Empty*"
            
            view = discord.ui.View()
            boton_id = discord.ui.Button(
                label=f"ID: {value}", 
                style=discord.ButtonStyle.secondary,
                disabled=True
            )
            view.add_item(boton_id)
            
            await interaction.response.send_message(
                formato, 
                view=view, 
                allowed_mentions=discord.AllowedMentions.none()
            )
        except Exception as e:
            return await interaction.response.send_message(f"> ❌ Error reading log database: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LogHistory(bot))
