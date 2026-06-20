import discord
from discord.ext import commands
from datetime import datetime
from logs.log_writer import LogWriter

class MessageLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1366171674239832104
        self.log_writer = LogWriter()

    def generate_message_link(self, message):
        if not message.guild:  # Si es DM, no hay link
            return "`[Mensaje Directo]`"
        return f"🔗 https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

    async def send_to_log_channel(self, message, is_dm=False):
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel is None:
            print("❌ Log channel not found.")
            return

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        if is_dm:
            embed.title = "📨 Mensaje Directo"
        else:
            embed.title = f"📨 Mensaje en {message.guild.name}"
            embed.add_field(name="Canal", value=f"<#{message.channel.id}>", inline=False)
            embed.add_field(name="Enlace", value=self.generate_message_link(message), inline=False)

        embed.add_field(name="Autor", value=f"{message.author.mention} (ID: {message.author.id})", inline=False)
        embed.add_field(name="Contenido", value=message.content or "*Sin contenido de texto*", inline=False)

        if message.attachments:
            embed.add_field(
                name="Archivos adjuntos",
                value="\n".join([f"[{a.filename}]({a.url})" for a in message.attachments]),
                inline=False
            )

        if message.embeds:
            embed.add_field(name="Embeds", value=f"{len(message.embeds)} embed(s) adjunto(s)", inline=False)

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        # Escribir en archivos de log
        try:
            self.log_writer.write_basic_log(message)
            self.log_writer.write_detailed_log(message)
            self.log_writer.write_channel_log(message)
        except Exception as e:
            print(f"❌ Error al escribir logs: {e}")

        '''if message.guild:
            print(f"\n📨 [Servidor] {message.guild.name} | Canal: #{message.channel.id}")
            print(f"🔗 https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}")
        else:
            print(f"\n📨 [Mensaje Directo]")
        
        print(f"👤 {message.author} (ID: {message.author.id})")
        print(f"📝 Contenido: {message.content}")'''

        # Enviar logs al canal de Discord
        try:
            await self.send_to_log_channel(message, is_dm=not message.guild)
        except Exception as e:
            print(f"❌ Error sending log: {e}")

        # Filtros adicionales
        if message.author.bot or message.content.startswith('.bc'):
            return

async def setup(bot):
    await bot.add_cog(MessageLogger(bot))