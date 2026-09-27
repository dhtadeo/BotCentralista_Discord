import discord
from discord import app_commands
from discord.ext import commands

class UserInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="user", 
        description="Shows a user's info"
    )
    @app_commands.describe(
        username="The user you want to fetch data (leave it blank to see yours)"
    )
    async def user_info(self, interaction: discord.Interaction, username: discord.Member = None):
        member = username or interaction.user

        embed = discord.Embed(
            title=f"{member.display_name}'s info", 
            color=member.color
        )
        
        if member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="👤 User", value=f"{member.name}", inline=True)
        embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="🤖 Is Bot", value="Yes" if member.bot else "No", inline=True)

        creation_ts = int(member.created_at.timestamp())
        embed.add_field(
            name="📅 Account created", 
            value=f"<t:{creation_ts}:F>\n(<t:{creation_ts}:R>)", 
            inline=True
        )

        if member.joined_at:
            joining_ts = int(member.joined_at.timestamp())
            embed.add_field(
                name="📥 Joined the server", 
                value=f"<t:{joining_ts}:F>\n(<t:{joining_ts}:R>)", 
                inline=True
            )

        roles = [rol.mention for rol in reversed(member.roles) if rol.name != "@everyone"]
        
        if roles:
            roles_text = " ".join(roles)
            if len(roles_text) > 1024:
                roles_text = roles_text[:1020] + "..."
            embed.add_field(name=f"🎭 Roles ({len(roles)})", value=roles_text, inline=False)
        else:
            embed.add_field(name="🎭 Roles (0)", value="*No assigned roles*", inline=False)

        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}", 
            icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(UserInfo(bot))
