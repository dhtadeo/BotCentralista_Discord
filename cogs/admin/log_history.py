import discord
from discord.ext import commands
import os
import json
import sqlite3
from cogs.admin._admin_config import ADMIN_PREFIX, get_authorized_users, UNAUTHORIZED_MESSAGE

class LogHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_prefix = ADMIN_PREFIX
        self.authorized_users = get_authorized_users()
        
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(cog_dir)) 
        self.db_path = os.path.join(root_dir, "logs", "bc_logs.db")

    @commands.command(name="loghistory", aliases=["lh"])
    async def log_history(self, ctx, value: str = None):
        if ctx.author.id not in self.authorized_users:
            await ctx.message.delete()
            return await ctx.send(UNAUTHORIZED_MESSAGE, delete_after=5)

        if not os.path.exists(self.db_path):
            return await ctx.send("> ⚠️ Log database not found on the system.", delete_after=5)

        value_int = None
        if value is not None:
            try:
                value_int = int(value)
            except ValueError:
                return await ctx.send("> ❌ The value must be a valid number.", delete_after=5)
                
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_lines = cursor.fetchone()[0]
            
            if total_lines == 0:
                conn.close()
                return await ctx.send("> ⚠️ Surprisingly, there are no logged messages yet...")
            
            if value_int is not None:
                if value_int <= 0 or value_int > total_lines:
                    conn.close()
                    return await ctx.send(f"> ❌ Value must be in between **1** and **{total_lines}**.")
                
                offset = value_int - 1
                cursor.execute("SELECT content, attachments, channel_id FROM messages LIMIT 1 OFFSET ?", (offset,))
                row = cursor.fetchone()
                conn.close()

                if not row:
                    return await ctx.send("> ❌ Message not found.")

                content_raw, attachments_raw, channel_id = row[0], row[1], row[2]
                selected_value = value_int
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
                    return await ctx.send("> ⚠️ No available messages to display...")

                selected_value, content_raw, attachments_raw, channel_id = row[0], row[1], row[2], row[3]

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
                label=f"ID: {selected_value}", 
                style=discord.ButtonStyle.secondary,
                disabled=True
            )
            view.add_item(boton_id)
            
            await ctx.send(
                formato, 
                view=view, 
                allowed_mentions=discord.AllowedMentions.none()
            )
        except Exception as e:
            return await ctx.send(f"> ❌ Error reading log database: `{e}`")

async def setup(bot):
    await bot.add_cog(LogHistory(bot))