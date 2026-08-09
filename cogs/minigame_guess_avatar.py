import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import sqlite3
import random
import os
import io

class GuessAvatarView(discord.ui.View):
    def __init__(self, author_id: int, correct_name: str, options: list):
        super().__init__(timeout=10.0)
        self.author_id = author_id
        self.correct_name = correct_name
        self.message = None

        for option_name in options:
            button = discord.ui.Button(
                label=option_name,
                style=discord.ButtonStyle.primary
            )
            button.callback = self.make_callback(option_name)
            self.add_item(button)

    def make_callback(self, option_name: str):
        async def button_callback(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message(
                    "> ❌ You cannot play someone else's game!", 
                    ephemeral=True
                )
                return

            for child in self.children:
                child.disabled = True

            if option_name == self.correct_name:
                embed = discord.Embed(
                    title="🎉 Correct!",
                    description=f"> You guessed it! The avatar belonged to **{self.correct_name}**.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="❌ Wrong Answer!",
                    description=f"> You picked **{option_name}**, but the avatar actually belonged to **{self.correct_name}**.",
                    color=discord.Color.red()
                )

            embed.set_image(url="attachment://avatar.png")

            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()

        return button_callback

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="⏰ Time's Up!",
            description=f"> You ran out of time! The avatar belonged to **{self.correct_name}**.",
            color=discord.Color.dark_gray()
        )

        embed.set_image(url="attachment://avatar.png")

        if self.message:
            try:
                await self.message.edit(embed=embed, view=self)
            except Exception:
                pass


class GuessAvatarGame(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(os.path.dirname(cog_dir), "logs", "bc_logs.db")

    @app_commands.command(
        name="minigame-guess-the-avatar", 
        description="Guess which user belongs to the profile picture shown"
    )
    async def guess_the_avatar(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not os.path.exists(self.db_path):
            return await interaction.followup.send("> ❌ Database not found.")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            rows = []
            filter_mode = "server"

            # Get users by server where command got executed
            if interaction.guild:
                cursor.execute("""
                    SELECT DISTINCT u.name, u.icon 
                    FROM users u
                    JOIN messages m ON u.user_id = m.user_id
                    WHERE m.server_id = ? 
                    AND u.name != 'Unknown' 
                    AND u.icon IS NOT NULL 
                    AND u.icon != '' 
                    AND u.is_bot = 0
                    ORDER BY RANDOM() 
                    LIMIT 30
                """, (interaction.guild.id,))
                rows = cursor.fetchall()

            # If there's less than 10 users in the database filter by everything
            if len(rows) < 10:
                filter_mode = "global"
                cursor.execute("""
                    SELECT DISTINCT name, icon FROM users 
                    WHERE name != 'Unknown' 
                    AND icon IS NOT NULL 
                    AND icon != '' 
                    AND is_bot = 0
                    ORDER BY RANDOM() 
                    LIMIT 30
                """)
                rows = cursor.fetchall()

            conn.close()

            if len(rows) < 3:
                return await interaction.followup.send("> ❌ Not enough distinct users in the database to start the minigame.")

            correct_name = None
            correct_icon = None
            image_bytes = None

            async with aiohttp.ClientSession() as session:
                for candidate in rows:
                    name, icon = candidate[0], candidate[1]
                    try:
                        async with session.get(icon, timeout=3) as resp:
                            if resp.status == 200:
                                image_bytes = await resp.read()
                                correct_name = name
                                correct_icon = icon
                                break
                    except Exception:
                        continue

            if not image_bytes or not correct_name:
                return await interaction.followup.send("> ❌ Couldn't load a valid avatar image for the minigame.")

            incorrect_candidates = [r[0] for r in rows if r[0] != correct_name]
            incorrect_candidates = list(dict.fromkeys(incorrect_candidates))

            if len(incorrect_candidates) < 2:
                return await interaction.followup.send("> ❌ Not enough distinct option candidates found.")

            selected_incorrect = random.sample(incorrect_candidates, 2)

            options = [correct_name, selected_incorrect[0], selected_incorrect[1]]
            random.shuffle(options)

            file = discord.File(io.BytesIO(image_bytes), filename="avatar.png")

            footer_text = f"Requested by {interaction.user.display_name} • You have 10s"
            if filter_mode == "server":
                footer_text += " • Mode: Server Users"
            else:
                footer_text += " • Mode: Global Users"

            embed = discord.Embed(
                title="❓ Guess the Avatar!",
                description="> Whose profile picture is this? Pick an option below!",
                color=discord.Color.blurple()
            )
            embed.set_image(url="attachment://avatar.png")
            embed.set_footer(text=footer_text)

            view = GuessAvatarView(
                author_id=interaction.user.id, 
                correct_name=correct_name, 
                options=options
            )

            msg = await interaction.followup.send(embed=embed, file=file, view=view)
            view.message = msg

        except Exception as e:
            await interaction.followup.send(f"> ❌ Error starting the minigame: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(GuessAvatarGame(bot))
