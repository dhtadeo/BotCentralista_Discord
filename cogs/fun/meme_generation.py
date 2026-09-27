import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import markovify
import os
import random
import textwrap

class MemeGenerator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        cog_dir = os.path.dirname(os.path.abspath(__file__))

        root_dir = os.path.dirname(os.path.dirname(cog_dir))
        self.font_path = os.path.join(root_dir, "fonts", "impact.ttf")

    def _get_markov_models(self, interaction: discord.Interaction):
        data = getattr(self.bot, 'global_chat_data', [])
        if not data:
            return None, None

        channel_msgs = []
        server_msgs = []

        guild_id = interaction.guild.id if interaction.guild else None
        channel_id = interaction.channel.id if interaction.channel else None

        for msg in data:
            if guild_id and msg.get("server_id") == guild_id:
                texto_msg = msg.get("content", "").strip()
                adjuntos = msg.get("attachments", [])
                if texto_msg or adjuntos:
                    linea = texto_msg
                    if adjuntos:
                        linea += " " + " ".join(adjuntos)
                    linea = linea.strip()
                    server_msgs.append(linea)
                    if channel_id and msg.get("channel_id") == channel_id:
                        channel_msgs.append(linea)

            elif not guild_id and channel_id and msg.get("channel_id") == channel_id:
                texto_msg = msg.get("content", "").strip()
                adjuntos = msg.get("attachments", [])
                if texto_msg or adjuntos:
                    linea = texto_msg
                    if adjuntos:
                        linea += " " + " ".join(adjuntos)
                    channel_msgs.append(linea.strip())

        def _create_model(mensajes):
            texto = "\n".join(mensajes)
            if not texto.strip() or len(texto.splitlines()) < 5:
                return None
            try:
                return markovify.NewlineText(texto, well_formed=False)
            except Exception:
                return None

        model_channel = _create_model(channel_msgs)
        model_server = _create_model(server_msgs) if guild_id else None

        return model_channel, model_server

    def _generate_sentence(self, model_channel, model_server):
        if model_channel:
            for _ in range(50):
                sentence = model_channel.make_sentence()
                if sentence:
                    return sentence

        if model_server:
            for _ in range(50):
                sentence = model_server.make_sentence()
                if sentence:
                    return sentence

        return None

    async def _get_valid_image(self, interaction: discord.Interaction):
        candidate_urls = []

        if interaction.guild:
            members = [m for m in interaction.guild.members if m.display_avatar]
            if members:
                candidate_urls.extend([random.choice(members).display_avatar.url for _ in range(20)])

        try:
            async for msg in interaction.channel.history(limit=100):
                if msg.author.id == self.bot.user.id:
                    continue
                    
                for att in msg.attachments:
                    if att.content_type and att.content_type.startswith('image/'):
                        candidate_urls.append(att.url)
        except Exception:
            pass

        chat_data = getattr(self.bot, 'global_chat_data', [])
        server_urls = []
        guild_id = interaction.guild.id if interaction.guild else None
        channel_id = interaction.channel.id if interaction.channel else None

        for msg in chat_data:
            is_valid = (guild_id and msg.get("server_id") == guild_id) or (not guild_id and channel_id and msg.get("channel_id") == channel_id)
            if is_valid:
                for att in msg.get("attachments", []):
                    url_limpia = att.lower().split('?')[0]
                    if any(url_limpia.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                        server_urls.append(att)
                    
        if server_urls:
            samples = min(40, len(server_urls))
            candidate_urls.extend(random.sample(server_urls, samples))

        random.shuffle(candidate_urls)

        async with aiohttp.ClientSession() as session:
            for url in candidate_urls:
                try:
                    async with session.get(url, timeout=2) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            return io.BytesIO(image_bytes)
                except Exception:
                    continue
                    
        return None

    def _create_meme_image(self, image_bytes, top_text, bottom_text=None):
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

        new_height = height + top_box_height + bottom_box_height
        canvas = Image.new("RGBA", (width, new_height), "white")
        
        canvas.paste(img, (0, top_box_height))
        draw = ImageDraw.Draw(canvas)

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
        canvas.convert("RGB").save(output, format="JPEG", quality=90)
        output.seek(0)
        return output

    @app_commands.command(name="meme", description="Generates a bad random meme")
    @app_commands.describe(image_content="Attach a random image")
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
            image_bytes = await self._get_valid_image(interaction)

        if not image_bytes:
            return await interaction.followup.send("> ❌ No available image was found, you can try again or send your own image.")

        model_channel, model_server = self._get_markov_models(interaction)

        top_text = self._generate_sentence(model_channel, model_server)
        if not top_text:
            top_text = "I need more context to generate a caption text..."

        bottom_text = None
        if random.choice([True, False]):
            candidate_bottom = self._generate_sentence(model_channel, model_server)
            if candidate_bottom and candidate_bottom != top_text:
                bottom_text = candidate_bottom

        try:
            meme_final = self._create_meme_image(image_bytes, top_text, bottom_text)
            await interaction.followup.send(file=discord.File(fp=meme_final, filename="meme_markovify.jpg"))
        except Exception as e:
            await interaction.followup.send(f"> ❌ Error sending meme: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(MemeGenerator(bot))