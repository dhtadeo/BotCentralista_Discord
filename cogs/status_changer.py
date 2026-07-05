import discord
from discord.ext import commands, tasks
import random

class StatusRotation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.rotate_status.start()

    def cog_unload(self):
        self.rotate_status.cancel()

    @tasks.loop(minutes=5)
    async def rotate_status(self):
        total_servers = len(self.bot.guilds)
        total_users = sum(guild.member_count for guild in self.bot.guilds if guild.member_count)
        
        datos_chat = getattr(self.bot, 'global_chat_data', [])
        total_messages = len(datos_chat)

        status = [
            discord.CustomActivity(name=f"{total_messages} dead molas..."),
            discord.CustomActivity(name=f"Invading {total_servers} servers"),
            discord.CustomActivity(name=f"{total_users} are not happy. Be happy!"),
            discord.CustomActivity(name="People be complaining about billionaires they're lucky I'm not a billionaire"),
            discord.CustomActivity(name="Minisugis, ¡me golpearon!"),
            discord.CustomActivity(name="Loser! Get a life!"),
            discord.CustomActivity(name="It's starting to come out"),
            discord.CustomActivity(name="I'm done with being nice to folks"),
            discord.CustomActivity(name="We will heal. We will repay, saith the Lord."),
            discord.CustomActivity(name="FIRE IN THE HOLE!"),
            discord.CustomActivity(name="Shine On, You Crazy Diamond"),
            discord.CustomActivity(name="Heehee... That's funny!"),
            discord.CustomActivity(name="HE'S RED FOR AN AMAZING REASON!"),
            discord.CustomActivity(name="Address the elephant in the room"),
            discord.CustomActivity(name="Waxed Lightly Weathered Cut Copper Stairs"),
            discord.CustomActivity(name="Knowledge from comics is still knowledge!"),
            discord.CustomActivity(name="I was born as a weeb, you merely adopted the anime life"),
            discord.CustomActivity(name="Anyone who disagrees with any of my opinions has autism"),
            discord.CustomActivity(name="Whether homeless or people, it's the weirdos who make life interesting"),
            discord.CustomActivity(name="No blind people. This place is for certified #Seers and #Lookers only."),
            discord.CustomActivity(name="Poop"),
            discord.CustomActivity(name="Live your zestiest most bestiest life"),
            discord.CustomActivity(name=f"{total_messages} x {total_servers} = {total_messages * total_servers}"),
            discord.CustomActivity(name="This poor generation has no tolerable future"),
            discord.CustomActivity(name="1984"),
            discord.CustomActivity(name="Roast meat, not cities"),
            discord.CustomActivity(name="Endless forms, most beautiful")
            # I will change this format later...
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
