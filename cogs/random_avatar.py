import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import sqlite3
import os
import io

class RandomImage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(os.path.dirname(cog_dir), "logs", "bc_logs.db")

    @app_commands.command(
        name="random-avatar", 
        description="(Testing) Shows a random user profile picture."
    )
    async def random_image(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not os.path.exists(self.db_path):
            return await interaction.followup.send("> ❌ Database not found.")

        try:
            # 1. Consultar a SQLite por avatares directamente
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Filtramos los Unknown, exigimos que haya un icono y sacamos una muestra de 20 al azar
            cursor.execute("""
                SELECT icon FROM users 
                WHERE name != 'Unknown' 
                AND icon IS NOT NULL 
                AND icon != '' 
                ORDER BY RANDOM() 
                LIMIT 20
            """)
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return await interaction.followup.send("> ❌ No valid profile pictures found in the database.")

            # Extraemos la lista de URLs
            image_urls = [row[0] for row in rows]

            # 2. Comprobamos rápidamente cuál sigue activa
            async with aiohttp.ClientSession() as session:
                for url in image_urls:
                    try:
                        # Hacemos la petición (si el usuario cambió de foto, el link viejo podría fallar)
                        async with session.get(url, timeout=3) as resp:
                            if resp.status == 200:
                                image_bytes = await resp.read()
                                
                                # Extraemos la extensión real de la URL, si no se detecta ponemos .png
                                ext = url.split('?')[0].split('.')[-1]
                                if ext not in ['png', 'jpg', 'jpeg', 'webp', 'gif']:
                                    ext = 'png'
                                    
                                filename = f"random_avatar.{ext}"

                                # 3. Enviamos la imagen viva y finalizamos el comando
                                await interaction.followup.send(
                                    file=discord.File(io.BytesIO(image_bytes), filename=filename)
                                )
                                return
                    except Exception:
                        continue # Si hay error o timeout, probamos el siguiente avatar de la lista
            
            # Si el bucle procesa los 20 avatares y todos fallan
            await interaction.followup.send("> ❌ Couldn't download a valid image after multiple attempts.")

        except Exception as e:
            await interaction.followup.send(f"> ❌ Database error: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(RandomImage(bot))
