import discord
from discord.ext import commands
from datetime import datetime
from logs.log_writer import LogWriter

class MessageLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_writer = LogWriter()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        try:
            self.log_writer.write_log(message)
        except Exception as e:
            print(f"[Logger] ❌ Error writing to database: {e}")        

async def setup(bot):
    await bot.add_cog(MessageLogger(bot))
