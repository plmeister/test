from discord.ext import commands
import discord

class Count(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def test_counter(self, ctx, message: str, count: int):
        view = discord.ui.View()
        view.add_item(CounterButton(message, discord.ButtonStyle.green, count))
        await ctx.send(message, view=view)
    
class CounterButton(discord.ui.Button):
    def __init__(self, label: str, style: discord.ButtonStyle, counter: int):
        super().__init__(label=label.replace('%', str(counter)), style=style)
        self.message = label
        self._count = counter
        self.responses = []

    async def callback(self, interaction: discord.Interaction):
        if interaction.user in self.responses:
            await interaction.response.send_message("You already clicked", delete_after=2)
            return

        self.responses.append(interaction.user)
        self._count -= 1
        if self._count <= 0:
            self.style = discord.ButtonStyle.red
            self.disabled = True
            await interaction.response.send_message(str(self.responses))
            return

        self.label = self.message.replace('%', str(self._count))
        await interaction.response.edit_message(view=self.view)
