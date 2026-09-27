import discord
from discord import app_commands
from discord.ext import commands
import markovify

class GenerateMessageServer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="generate-message-server", 
        description="Generates a coherent message based on all messages sent in this server"
    )
    async def generate_message_server(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not interaction.guild:
            return await interaction.followup.send("> ❌ This command can only be used inside a server.")

        data = getattr(self.bot, 'global_chat_data', [])
        
        if not data:
            return await interaction.followup.send("> ⚠️ Failed to generate a message. Data is still loading.")

        try:
            messages = []
            for msg in data:
                if msg.get("server_id") == interaction.guild.id:
                    text_msg = msg.get("content", "").strip()
                    attachments = msg.get("attachments", [])
                    
                    if text_msg or attachments:
                        line = text_msg
                        if attachments:
                            line += " " + " ".join(attachments)
                        messages.append(line.strip())
                        
            text = "\n".join(messages)
                
            if not text.strip() or len(text.splitlines()) < 5:
                return await interaction.followup.send("> ❌ Not enough messages stored for this server yet. Lock in!")

            model = markovify.NewlineText(text, well_formed=False)
            
            sentence = None
            for _ in range(50):
                sentence = model.make_sentence()
                if sentence: break

            if sentence:
                await interaction.followup.send(
                    sentence,
                    allowed_mentions=discord.AllowedMentions.none()
                )
            else:
                await interaction.followup.send("> ⚠️ Couldn't generate a message after many tries...")

        except Exception as e:
            await interaction.followup.send(f"> ❌ Error: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(GenerateMessageServer(bot))
