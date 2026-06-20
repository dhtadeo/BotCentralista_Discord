import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class Say_Command(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
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
            print("⚠️ `config.json` not found.")
            return set()

    async def get_webhook(self, channel):
        webhooks = await channel.webhooks()
        for webhook in webhooks:
            if webhook.user == self.bot.user:
                return webhook
        return await channel.create_webhook(name="Bot Say Webhook")

    @app_commands.command(name='say', description="Bot says something for you.")
    @app_commands.describe(
        say_something="Input some text.",
        impersonate="Pick a user to spoof.",
        attachment="Attach media."
    )
    async def say(self, interaction: discord.Interaction, say_something: str = None, impersonate: discord.Member = None, attachment: discord.Attachment = None):
        
        if not say_something and not attachment:
            await interaction.response.send_message("❌ There should be at least content in `say_something` or `attachment` to send the message.", ephemeral=True)
            return

        if impersonate and interaction.user.id not in self.authorized_users:
            await interaction.response.send_message("❌ `impersonate` is currently disabled, will be enabled for use in a future update.", ephemeral=True)
            return
        
        await interaction.response.send_message("⚠️ Maybe the message was sent or not, wait for something to happen.", ephemeral=True)

        file_to_send = await attachment.to_file() if attachment else None

        kwargs = {}
        if say_something:
            kwargs['content'] = say_something
        if file_to_send:
            kwargs['file'] = file_to_send

        if not impersonate:
            await interaction.channel.send(**kwargs)
            return

        if isinstance(interaction.channel, discord.TextChannel):
            try:
                webhook = await self.get_webhook(interaction.channel)
                
                kwargs['username'] = impersonate.display_name
                kwargs['avatar_url'] = impersonate.display_avatar.url
                
                await webhook.send(**kwargs)
                
            except discord.Forbidden:
                await interaction.followup.send("❌ **Manage Webhooks** permission required.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ Error sending Webhook: {e}", ephemeral=True)
        else:
            await interaction.channel.send(**kwargs)

async def setup(bot: commands.Bot):
    await bot.add_cog(Say_Command(bot))