import discord
from discord.ext import commands
import markovify

class BotMentionReply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

            # Entrena y genera base en lista de mensajes
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
            
            if oracion_final:
                try:
                    await message.reply(
                        oracion_final, 
                        allowed_mentions=discord.AllowedMentions.none()
                    )
                except Exception as e:
                    print(f"[Autoreply] ❌ Autoreply error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(BotMentionReply(bot))