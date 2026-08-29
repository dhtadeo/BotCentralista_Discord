import discord
from discord import app_commands
from discord.ext import commands

class Say_Command(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='say', description="Your good friend Bot Centralista will say something for you")
    @app_commands.describe(
        text="Input some text",
        attachment="Attach media"
    )
    async def say(self, interaction: discord.Interaction, text: str = None, attachment: discord.Attachment = None):
        
        if not text and not attachment:
            await interaction.response.send_message("> ❌ There should be at least content in `text` or `attachment` to send the message.", ephemeral=True)
            return

        await interaction.response.send_message("> ✅ The message was sent.", ephemeral=True)

        file_to_send = await attachment.to_file() if attachment else None

        kwargs = {}
        if text:
            kwargs['content'] = text
        if file_to_send:
            kwargs['file'] = file_to_send

        kwargs['allowed_mentions'] = discord.AllowedMentions.none()
        
        view = discord.ui.View()
        boton_autor = discord.ui.Button(
            label=f"{interaction.user.display_name}",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        view.add_item(boton_autor)
        kwargs['view'] = view

        # Envío del mensaje
        await interaction.channel.send(**kwargs)

async def setup(bot: commands.Bot):
    await bot.add_cog(Say_Command(bot))