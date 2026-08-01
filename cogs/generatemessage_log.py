import discord
from discord import app_commands
from discord.ext import commands
import markovify

class GenerateMessageLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="generate-message-log", description="Generates a random coherent message using logs and some magic.")
    async def generate_message_log(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if getattr(self.bot, 'global_markov_model', None) is None:
            return await interaction.followup.send("> ⚠️ Interaction failed, please try again in a few moments.")

        try:
            oracion = None
            for _ in range(50):
                oracion = self.bot.global_markov_model.make_sentence()
                if oracion: break

            if oracion:
                await interaction.followup.send(
                    oracion, 
                    allowed_mentions=discord.AllowedMentions.none()
                )
            else:
                await interaction.followup.send("⚠️ Couldn't generate a coherent message after multiple tries.")
        except Exception as e:
            await interaction.followup.send(f"> ❌ Error generating message: `{e}`")

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
            data = getattr(self.bot, 'global_chat_data', [])
            oracion_final = None

            # Train and generate
            def intentar_generar(lista_mensajes):
                texto = "\n".join(lista_mensajes)
                if not texto.strip() or len(texto.splitlines()) < 5:
                    return None
                try:
                    modelo = markovify.NewlineText(texto, well_formed=False)
                    for _ in range(50):
                        oracion = modelo.make_sentence()
                        if oracion: return oracion
                except:
                    pass
                return None

            # Get filtered messages
            if data:
                canal_msgs = []
                server_msgs = []

                for msg in data:
                    if message.guild and msg.get("server_id") == message.guild.id:
                        # From this server
                        texto_msg = msg.get("content", "").strip()
                        adjuntos = msg.get("attachments", [])
                        if texto_msg or adjuntos:
                            linea = texto_msg
                            if adjuntos: linea += " " + " ".join(adjuntos)
                            linea = linea.strip()
                            
                            server_msgs.append(linea)
                            # From this channel
                            if msg.get("channel_id") == message.channel.id:
                                canal_msgs.append(linea)
                    
                    elif not message.guild and msg.get("channel_id") == message.channel.id:
                        # If DM
                        texto_msg = msg.get("content", "").strip()
                        adjuntos = msg.get("attachments", [])
                        if texto_msg or adjuntos:
                            linea = texto_msg
                            if adjuntos: linea += " " + " ".join(adjuntos)
                            canal_msgs.append(linea.strip())

                # LEVEL 1: Channel messages
                oracion_final = intentar_generar(canal_msgs)

                # LEVEL 2: Server messages
                if not oracion_final and message.guild:
                    oracion_final = intentar_generar(server_msgs)

            # LEVEL 3: Log messages (if LEVEL 1 and 2 failed to generate a message)
            if not oracion_final and getattr(self.bot, 'global_markov_model', None) is not None:
                try:
                    for _ in range(50):
                        oracion_final = self.bot.global_markov_model.make_sentence()
                        if oracion_final: break
                except:
                    pass

            if oracion_final:
                try:
                    await message.reply(
                        oracion_final, 
                        allowed_mentions=discord.AllowedMentions.none()
                    )
                except Exception as e:
                    print(f"[Autoreply] ❌ Autoreply error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(GenerateMessageLog(bot))
