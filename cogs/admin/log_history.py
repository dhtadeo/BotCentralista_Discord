import discord
from discord.ext import commands
import os
import json
import sqlite3
from cogs.admin._admin_config import ADMIN_PREFIX, get_authorized_users, UNAUTHORIZED_MESSAGE

def format_log_message(content_raw, attachments_raw):
    attachments_list = []
    if attachments_raw:
        try:
            attachments_list = json.loads(attachments_raw)
        except Exception:
            attachments_list = []

    content_text = content_raw.strip() if content_raw else ""

    if content_text and attachments_list:
        return f"{content_text}\n " + "\n ".join(attachments_list)
    elif content_text:
        return content_text
    elif attachments_list:
        return "\n ".join(attachments_list)
    else:
        return "*Empty*"


def fetch_random_log(db_path):
    conn = sqlite3.connect(db_path, timeout=5.0)
    cursor = conn.cursor()
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
    return row

class ShuffleView(discord.ui.View):
    def __init__(self, author_id: int, db_path: str, initial_id: int, include_shuffle: bool = False):
        super().__init__(timeout=30.0 if include_shuffle else None)
        self.author_id = author_id
        self.db_path = db_path
        self.message = None

        self.boton_id = discord.ui.Button(
            label=f"ID: {initial_id}",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        self.add_item(self.boton_id)

        self.boton_shuffle = None
        if include_shuffle:
            self.boton_shuffle = discord.ui.Button(
                label="Shuffle",
                style=discord.ButtonStyle.success
            )
            self.boton_shuffle.callback = self.shuffle_callback
            self.add_item(self.boton_shuffle)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "> ❌ Only the user who summoned this command can use this button.",
                ephemeral=True
            )
            return False
        return True

    async def shuffle_callback(self, interaction: discord.Interaction):
        try:
            row = fetch_random_log(self.db_path)
            if not row:
                return await interaction.response.send_message(
                    "> ⚠️ No available messages to display...",
                    ephemeral=True
                )

            selected_value, content_raw, attachments_raw, _ = row[0], row[1], row[2], row[3]
            formats = format_log_message(content_raw, attachments_raw)

            self.boton_id.label = f"ID: {selected_value}"

            await interaction.response.edit_message(
                content=formats,
                view=self,
                allowed_mentions=discord.AllowedMentions.none()
            )
        except Exception as e:
            await interaction.response.send_message(
                f"> ❌ Error reading log database: `{e}`",
                ephemeral=True
            )

    async def on_timeout(self):
        if self.boton_shuffle is not None:
            self.boton_shuffle.disabled = True
            if self.message:
                try:
                    await self.message.edit(view=self)
                except discord.HTTPException:
                    pass

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
                conn.close()
                row = fetch_random_log(self.db_path)

                if not row:
                    return await ctx.send("> ⚠️ No available messages to display...")

                selected_value, content_raw, attachments_raw, channel_id = row[0], row[1], row[2], row[3]

            formats = format_log_message(content_raw, attachments_raw)
            
            view = ShuffleView(
                author_id=ctx.author.id,
                db_path=self.db_path,
                initial_id=selected_value,
                include_shuffle=(value_int is None)
            )
            
            sent_message = await ctx.send(
                formats, 
                view=view, 
                allowed_mentions=discord.AllowedMentions.none()
            )
            view.message = sent_message
        except Exception as e:
            return await ctx.send(f"> ❌ Error reading log database: `{e}`")

async def setup(bot):
    await bot.add_cog(LogHistory(bot))