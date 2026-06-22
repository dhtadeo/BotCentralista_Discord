import discord
from discord import app_commands
from discord.ext import commands

class GenerateMessageLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="gen-message-log", description="Generates a message using the global JSON brain.")
    async def generate_message_log(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Si el DataCore todavía no carga
        if getattr(self.bot, 'global_markov_model', None) is None:
            return await interaction.followup.send("⚠️ Bot core is starting, pleass try again in a few moments.")

        try:
            oracion = None
            for _ in range(50):
                oracion = self.bot.global_markov_model.make_sentence()
                if oracion: break

            if oracion:
                await interaction.followup.send(oracion, allowed_mentions=discord.AllowedMentions.none())
            else:
                await interaction.followup.send("⚠️ Couldn't generate a coherent message after multiple tries.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating message: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot: return

        bot_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = False
        
        if message.reference and message.reference.message_id:
            try:
                cached_msg = message.reference.cached_message
                if cached_msg and cached_msg.author == self.bot.user:
                    is_reply_to_bot = True
                elif not cached_msg:
                    replied_msg = await message.channel.fetch_message(message.reference.message_id)
                    if replied_msg.author == self.bot.user:
                        is_reply_to_bot = True
            except Exception:
                pass 

        if not (bot_mentioned or is_reply_to_bot):
            return

        async with message.channel.typing():
            if getattr(self.bot, 'global_markov_model', None) is None: return

            try:
                oracion = None
                for _ in range(50):
                    oracion = self.bot.global_markov_model.make_sentence()
                    if oracion: break

                if oracion:
                    mentions_config = discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False)
                    await message.reply(oracion, allowed_mentions=mentions_config)
            except Exception as e:
                print(f"❌ Error auto-responder: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(GenerateMessageLog(bot))