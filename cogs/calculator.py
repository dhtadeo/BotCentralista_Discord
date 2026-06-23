import discord
from discord import app_commands, ui
from discord.ext import commands

class CalculatorButtons(ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.expression = ""
    
    async def add(self, interaction: discord.Interaction, symbol):
        if self.expression == "...":
            self.expression = ""
        self.expression += symbol
        await self.update(interaction)

    async def update(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.message.edit(content=f"```{self.expression}```")

    async def solve(self, interaction: discord.Interaction):
        try:
            result = str(eval(self.expression.replace('pi', '3.14159')))
            self.expression = result
        except Exception as e:
            await interaction.response.send_message("> ⚠️ Buddy, your expresion is invalid!", ephemeral=True)
            self.expression = "..."
        await self.update(interaction)

    async def cleared(self, interaction: discord.Interaction):
        self.expression = "..."
        await self.update(interaction)

    @ui.button(label="clear", style=discord.ButtonStyle.red, row=0)
    async def clear(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.cleared(interaction)

    @ui.button(label="(", style=discord.ButtonStyle.blurple, row=0)
    async def p1(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "(")

    @ui.button(label=")", style=discord.ButtonStyle.blurple, row=0)
    async def p2(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, ")")

    @ui.button(label="/", style=discord.ButtonStyle.blurple, row=0)
    async def divide(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "/")

    @ui.button(label="7", style=discord.ButtonStyle.grey, row=1)
    async def s7(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "7")

    @ui.button(label="8", style=discord.ButtonStyle.grey, row=1)
    async def s8(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "8")

    @ui.button(label="9", style=discord.ButtonStyle.grey, row=1)
    async def s9(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "9")

    @ui.button(label="x", style=discord.ButtonStyle.blurple, row=1)
    async def multi(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "*")

    @ui.button(label="4", style=discord.ButtonStyle.grey, row=2)
    async def s4(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "4")

    @ui.button(label="5", style=discord.ButtonStyle.grey, row=2)
    async def s5(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "5")

    @ui.button(label="6", style=discord.ButtonStyle.grey, row=2)
    async def s6(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "6")

    @ui.button(label="-", style=discord.ButtonStyle.blurple, row=2)
    async def minus(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "-")

    @ui.button(label="1", style=discord.ButtonStyle.grey, row=3)
    async def s1(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "1")

    @ui.button(label="2", style=discord.ButtonStyle.grey, row=3)
    async def s2(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "2")

    @ui.button(label="3", style=discord.ButtonStyle.grey, row=3)
    async def s3(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "3")

    @ui.button(label="+", style=discord.ButtonStyle.blurple, row=3)
    async def plus(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "+")

    @ui.button(label=".", style=discord.ButtonStyle.grey, row=4)
    async def decimal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, ".")

    @ui.button(label="0", style=discord.ButtonStyle.grey, row=4)
    async def s0(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "0")

    @ui.button(label="π", style=discord.ButtonStyle.grey, row=4)
    async def pi(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.add(interaction, "pi")

    @ui.button(label="=", style=discord.ButtonStyle.green, row=4)
    async def equals(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.solve(interaction)

class Calculator_Command(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="calculator", description="Sends an interactive calculator.")
    async def calculator(self, interaction: discord.Interaction):
        view = CalculatorButtons()
        await interaction.response.send_message("# ```\n...\n```", view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Calculator_Command(bot))
