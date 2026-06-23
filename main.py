import os
import discord
import pathlib 
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()

class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='bc.',
            intents=discord.Intents().all(), 
            application_id = os.getenv('APP_ID'))
        
    async def setup_hook(self):
        cogs_path = pathlib.Path(__file__).parent / "cogs"
        for filename in os.listdir(cogs_path):
            if filename.endswith('.py') and not filename.startswith('_'):
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"[Commands] 🧮 {filename} loaded.")

    async def on_ready(self):
        print(f"[Bot] 🤖 Logged as: {self.user.name}")
        synced = await self.tree.sync()
        print(f"[Commands] 🧮 {str(len(synced))} commands synced.")
        print(f"[Bot] 🤖 Connected to {len(self.guilds)} servers:")
        print(f"[Bot] 🤖 {[guild.name for guild in self.guilds]}")

        channel_to_send = client.get_channel(1174602784541245490)
        await channel_to_send.send(f"Ok {str(len(synced))}.\nOk {len(self.guilds)}\n{[guild.name for guild in self.guilds]}")

client = Client()

client.run(os.getenv('DISCORD_TOKEN'))