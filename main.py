import json
import os
import discord
import pathlib 
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()

CONFIG_PATH = pathlib.Path(__file__).with_name("config.json")
with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
    config = json.load(config_file)
    LOGS_CHANNEL_ID = config.get("logs_channel", [None])[0]

class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='bc.',
            intents=discord.Intents().all(), 
            application_id = os.getenv('APP_ID'))
        
    async def setup_hook(self):
        cogs_path = pathlib.Path(__file__).parent / "cogs"
        
        # Check for all .py files in the cogs directory and load them as extensions
        for item in os.listdir(cogs_path):
            item_path = cogs_path / item
            
            # 1. If the file is a Python file (not starting with '_'), load it as an extension
            if item_path.is_file() and item.endswith('.py') and not item.startswith('_'):
                await self.load_extension(f"cogs.{item[:-3]}")
                print(f"[Commands] 🧮 {item} loaded.")
                
            # 2. If the element is a directory
            elif item_path.is_dir() and not item.startswith(('_', '.')):
                for filename in os.listdir(item_path):
                    if filename.endswith('.py') and not filename.startswith('_'):
                        # Load the file using dot notation
                        await self.load_extension(f"cogs.{item}.{filename[:-3]}")
                        print(f"[Commands] 🧮 {item}/{filename} loaded.")

    async def on_ready(self):
        print(f"[Bot] 🤖 Logged as: {self.user.name}")
        synced = await self.tree.sync()
        print(f"[Commands] 🧮 {str(len(synced))} commands synced.")
        print(f"[Bot] 🤖 Connected to {len(self.guilds)} servers:")
        print(f"[Bot] 🤖 {[guild.name for guild in self.guilds]}")

        channel_to_send = self.get_channel(LOGS_CHANNEL_ID)
        await channel_to_send.send(f"**{str(len(synced))}** commands synced. \n**{len(self.guilds)}** servers:\n\n```{[guild.name for guild in self.guilds]}```")

client = Client()

client.run(os.getenv('DISCORD_TOKEN'))