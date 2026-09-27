import discord
from discord.ext import commands, tasks
import random

class StatusRotation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.rotate_status.start()

    def cog_unload(self):
        self.rotate_status.cancel()

    def _generate_markov_text(self):
        model = getattr(self.bot, 'global_markov_model', None)
        if not model:
            return "..."
        try:
            for _ in range(50):
                sentence = model.make_short_sentence(128) or model.make_sentence()
                if sentence:
                    return sentence.strip()[:128]
        except Exception:
            pass
        return "..."

    @tasks.loop(seconds=15)
    async def rotate_status(self):
        markov_text = self._generate_markov_text()
        status = [
            discord.CustomActivity(name=markov_text.capitalize())
        ]

        chosen_status = random.choice(status)

        try:
            await self.bot.change_presence(activity=chosen_status, status=discord.Status.dnd)
        except Exception as e:
            print(f"❌ [Status] Error changing bot status: {e}")

    @rotate_status.before_loop
    async def before_rotate(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(StatusRotation(bot))
