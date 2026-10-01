import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import os
import random
import json
import datetime

class FunShip(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(cog_dir)) 
        
        self.font_path = os.path.join(root_dir, "fonts", "LilitaOne-Regular.ttf")
        self.heart_empty_path = os.path.join(root_dir, "src", "HeartEmpty.png")
        self.heart_full_path = os.path.join(root_dir, "src", "HeartFull.png")
        self.messages_path = os.path.join(root_dir, "src", "ship_messages.json")

    def _get_ship_name(self, name1: str, name2: str) -> str:
        vowels = "aeiouAEIOU"
        
        split1 = len(name1) // 2
        for i, char in enumerate(name1[1:], 1):
            if char in vowels:
                split1 = i + 1
                break
                
        split2 = len(name2) // 2
        for i in range(len(name2)-2, 0, -1):
            if name2[i] in vowels:
                split2 = i
                break
                
        return (name1[:split1] + name2[split2:]).capitalize()

    def _get_random_message(self, percentage: int, is_self: bool = False) -> str:
        try:
            with open(self.messages_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if is_self:
                category = "self"
            elif percentage <= 25:
                category = "0-25"
            elif percentage <= 50:
                category = "26-50"
            elif percentage <= 75:
                category = "51-75"
            elif percentage <= 99:
                category = "76-99"
            else:
                category = "100"
                
            return random.choice(data.get(category, ["What a unique ship!"]))
        except Exception:
            return "Happy shipping!"

    async def _fetch_avatar(self, url: str) -> io.BytesIO:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    return io.BytesIO(await resp.read())
        return None

    def _create_circular_avatar(self, image_bytes: io.BytesIO, size: tuple = (150, 150)) -> Image.Image:
        img = Image.open(image_bytes).convert("RGBA").resize(size)
        
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        
        img.putalpha(mask)
        return img

    def _generate_ship_image(self, avatar1_bytes: io.BytesIO, avatar2_bytes: io.BytesIO, percentage: int) -> io.BytesIO:
        avatar_size = (150, 150)
        canvas_size = (500, 150)
        
        canvas = Image.new("RGBA", canvas_size, (255, 255, 255, 0))
        
        av1 = self._create_circular_avatar(avatar1_bytes, avatar_size)
        av2 = self._create_circular_avatar(avatar2_bytes, avatar_size)
        
        canvas.paste(av1, (0, 0), av1)
        canvas.paste(av2, (350, 0), av2)
        
        heart_empty = Image.open(self.heart_empty_path).convert("RGBA").resize(avatar_size)
        heart_full = Image.open(self.heart_full_path).convert("RGBA").resize(avatar_size)
        
        heart_x = 175
        canvas.paste(heart_empty, (heart_x, 0), heart_empty)
        
        crop_height = int(avatar_size[1] * (percentage / 100.0))
        if crop_height > 0:
            box = (0, avatar_size[1] - crop_height, avatar_size[0], avatar_size[1])
            cropped_heart = heart_full.crop(box)
            canvas.paste(cropped_heart, (heart_x, avatar_size[1] - crop_height), cropped_heart)
            
        draw = ImageDraw.Draw(canvas)
        text = f"{percentage}%"
        try:
            font = ImageFont.truetype(self.font_path, 40)
        except IOError:
            font = ImageFont.load_default()
            
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x_text = heart_x + (avatar_size[0] - text_w) / 2
        y_text = (avatar_size[1] - text_h) / 2 - 10
        
        outline_color = "black"
        for adj in [-2, -1, 1, 2]:
            draw.text((x_text+adj, y_text), text, font=font, fill=outline_color)
            draw.text((x_text, y_text+adj), text, font=font, fill=outline_color)
            draw.text((x_text+adj, y_text+adj), text, font=font, fill=outline_color)
            draw.text((x_text-adj, y_text+adj), text, font=font, fill=outline_color)
            
        draw.text((x_text, y_text), text, font=font, fill="white")
        
        output = io.BytesIO()
        canvas.save(output, format="PNG")
        output.seek(0)
        return output

    @app_commands.command(name="ship", description="Calculates the love percentage between two users.")
    @app_commands.describe(user1="First user", user2="Second user")
    async def ship(self, interaction: discord.Interaction, user1: discord.User, user2: discord.User):
        await interaction.response.defer()
        
        is_self = user1.id == user2.id
        
        if is_self:
            percentage = 100
            ship_name = user1.display_name
        else:
            tz_offset = datetime.timezone(datetime.timedelta(hours=-5))
            current_date = datetime.datetime.now(tz_offset).strftime("%Y%m%d")
            
            id_a, id_b = sorted([user1.id, user2.id])
            seed_val = int(f"{id_a}{id_b}{current_date}")
            
            random.seed(seed_val)
            percentage = random.randint(0, 100)
            random.seed()
            
            ship_name = self._get_ship_name(user1.display_name, user2.display_name)
        
        msg_text = self._get_random_message(percentage, is_self=is_self)
        avatar1_bytes = await self._fetch_avatar(user1.display_avatar.url)
        avatar2_bytes = await self._fetch_avatar(user2.display_avatar.url)
        
        if not avatar1_bytes or not avatar2_bytes:
            return await interaction.followup.send("> ❌ Failed to fetch user avatars.")
            
        final_image = self._generate_ship_image(avatar1_bytes, avatar2_bytes, percentage)
        
        embed = discord.Embed(
            title=f"💕 {ship_name} 💕",
            description=f"**{percentage}%** - {msg_text}",
            color=0xFF69B4
        )
        embed.set_image(url="attachment://ship.png")    
        
        await interaction.followup.send(
            embed=embed, 
            file=discord.File(fp=final_image, filename="ship.png")
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(FunShip(bot))