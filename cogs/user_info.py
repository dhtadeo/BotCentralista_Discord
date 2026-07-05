import discord
from discord import app_commands
from discord.ext import commands

class UserInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="user", 
        description="Shows a user's info."
    )
    @app_commands.describe(
        miembro="The user you want to fetch data (leave it blank to see yours)"
    )
    async def user_info(self, interaction: discord.Interaction, miembro: discord.Member = None):
        miembro = miembro or interaction.user

        embed = discord.Embed(
            title=f"{miembro.display_name}'s info", 
            color=miembro.color
        )
        
        if miembro.display_avatar:
            embed.set_thumbnail(url=miembro.display_avatar.url)

        embed.add_field(name="👤 User", value=f"{miembro.name}", inline=True)
        embed.add_field(name="🆔 ID", value=f"`{miembro.id}`", inline=True)
        embed.add_field(name="🤖 Is Bot", value="Sí" if miembro.bot else "No", inline=True)

        creacion_ts = int(miembro.created_at.timestamp())
        embed.add_field(
            name="📅 Account created", 
            value=f"<t:{creacion_ts}:F>\n(<t:{creacion_ts}:R>)", 
            inline=True
        )

        if miembro.joined_at:
            ingreso_ts = int(miembro.joined_at.timestamp())
            embed.add_field(
                name="📥 Joined the server", 
                value=f"<t:{ingreso_ts}:F>\n(<t:{ingreso_ts}:R>)", 
                inline=True
            )

        roles = [rol.mention for rol in reversed(miembro.roles) if rol.name != "@everyone"]
        
        if roles:
            roles_texto = " ".join(roles)
            if len(roles_texto) > 1024:
                roles_texto = roles_texto[:1020] + "..."
            embed.add_field(name=f"🎭 Roles ({len(roles)})", value=roles_texto, inline=False)
        else:
            embed.add_field(name="🎭 Roles (0)", value="*No assigned roles*", inline=False)

        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}", 
            icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(UserInfo(bot))
