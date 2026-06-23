import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import os
import random
import textwrap

class MemeGenerator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        self.font_path = os.path.join(os.path.dirname(cog_dir), "fonts", "impact.ttf")

    def _generar_texto(self):
        modelo = getattr(self.bot, 'global_markov_model', None)
        if not modelo:
            return "> ⚠️ Whoopsies"
        
        for _ in range(50):
            oracion = modelo.make_sentence()
            if oracion: return oracion
        return "Cuando el bot no sabe qué decir\npero hace un meme igual."

    async def _obtener_imagen_valida(self, interaction: discord.Interaction):
        urls_candidatas = []

        if interaction.guild:
            miembros = [m for m in interaction.guild.members if m.display_avatar]
            if miembros:
                urls_candidatas.extend([random.choice(miembros).display_avatar.url for _ in range(20)])

        try:
            async for msg in interaction.channel.history(limit=100):
                if msg.author.id == self.bot.user.id:
                    continue
                    
                for att in msg.attachments:
                    if att.content_type and att.content_type.startswith('image/'):
                        urls_candidatas.append(att.url)
        except Exception:
            pass

        datos_chat = getattr(self.bot, 'global_chat_data', [])
        urls_globales = []
        for msg in datos_chat:
            for att in msg.get("attachments", []):
                url_limpia = att.lower().split('?')[0]
                if any(url_limpia.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                    urls_globales.append(att)
                    
        if urls_globales:
            muestras = min(40, len(urls_globales))
            urls_candidatas.extend(random.sample(urls_globales, muestras))

        random.shuffle(urls_candidatas)

        async with aiohttp.ClientSession() as session:
            for url in urls_candidatas:
                try:
                    # Timeout corto para no hacer esperar al usuario
                    async with session.get(url, timeout=2) as resp:
                        if resp.status == 200: # El link está vivo y respondió con éxito
                            image_bytes = await resp.read()
                            return io.BytesIO(image_bytes)
                except Exception:
                    continue
                    
        return None

    def _crear_meme_imagen(self, image_bytes, top_text, bottom_text=None):
        img = Image.open(image_bytes).convert("RGBA")
        width, height = img.size

        font_size = max(20, int(width * 0.08))
        try:
            font = ImageFont.truetype(self.font_path, font_size)
        except IOError:
            font = ImageFont.load_default()

        caracteres_por_linea = int(width / (font_size * 0.45))
        top_lines = textwrap.wrap(top_text, width=caracteres_por_linea)
        bottom_lines = textwrap.wrap(bottom_text, width=caracteres_por_linea) if bottom_text else []

        line_height = font_size + 5
        padding = 20
        top_box_height = (len(top_lines) * line_height) + padding
        bottom_box_height = (len(bottom_lines) * line_height) + padding if bottom_lines else 0

        nueva_altura = height + top_box_height + bottom_box_height
        lienzo = Image.new("RGBA", (width, nueva_altura), "white")
        
        lienzo.paste(img, (0, top_box_height))
        draw = ImageDraw.Draw(lienzo)

        y_text = 10
        for line in top_lines:
            w = draw.textlength(line, font=font)
            draw.text(((width - w) / 2, y_text), line, font=font, fill="black")
            y_text += line_height

        if bottom_lines:
            y_text = height + top_box_height + 10
            for line in bottom_lines:
                w = draw.textlength(line, font=font)
                draw.text(((width - w) / 2, y_text), line, font=font, fill="black")
                y_text += line_height

        output = io.BytesIO()
        lienzo.convert("RGB").save(output, format="JPEG", quality=90)
        output.seek(0)
        return output

    @app_commands.command(name="meme", description="Generates a bad random meme")
    @app_commands.describe(image_content="Attach a random image.")
    async def meme(self, interaction: discord.Interaction, image_content: discord.Attachment = None):
        await interaction.response.defer()

        image_bytes = None

        if image_content and image_content.content_type and image_content.content_type.startswith('image/'):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_content.url, timeout=5) as resp:
                        if resp.status == 200:
                            image_bytes = io.BytesIO(await resp.read())
            except Exception:
                pass
                
        if not image_bytes:
            image_bytes = await self._obtener_imagen_valida(interaction)

        if not image_bytes:
            return await interaction.followup.send("> ❌ No available image was found, you can try again or send your own image.")

        texto_superior = self._generar_texto()
        texto_inferior = self._generar_texto() if random.choice([True, False]) else None

        try:
            meme_final = self._crear_meme_imagen(image_bytes, texto_superior, texto_inferior)
            await interaction.followup.send(file=discord.File(fp=meme_final, filename="meme_markovify.jpg"))
        except Exception as e:
            await interaction.followup.send(f"> ❌ Error sending meme: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(MemeGenerator(bot))