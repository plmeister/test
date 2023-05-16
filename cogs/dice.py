from discord.ext import commands
import discord
import random
from .. import checks

class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_enabled(self, guildid):
        settings = self.bot.get_cog('Settings')
        return await settings.is_cog_enabled(guildid, 'dice')

    @commands.hybrid_command()
    async def roll(self, ctx, dice: str):
        if not await self.is_enabled(ctx.guild.id):
            return
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await ctx.send('Format has to be NdN!')
            return

        result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.send(result)
