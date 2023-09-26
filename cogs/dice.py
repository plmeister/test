from discord.ext import commands
import random
import checks
import discord
from table2ascii import table2ascii as t2a, PresetStyle

class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_enabled(self, guildid):
        settings = self.bot.get_cog('Settings')
        return await settings.is_cog_enabled(guildid, 'dice')

    @commands.hybrid_command()
    async def roll(self, ctx, dice: str = "6"):
        if not await self.is_enabled(ctx.guild.id):
            return
        rolls = 1
        limit = 6
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            try:
                limit = int(dice)
            except Exception:
                await ctx.send(f"Couldn't work out what you meant by '/roll {dice}'")
                return

        result = f'{ctx.author.mention} used /roll {rolls}d{limit} and rolled: ' + ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.send(result)
        
        
    @commands.command()
    async def roll_for(self, ctx, dice: int, *members: discord.Member):
        if not await self.is_enabled(ctx.guild.id):
            return
        
        rolls = [[members[i].mention, random.randint(1, dice)] for i in range(len(members))]
        results = f"{ctx.author.mention} used roll_for {dice}\n" + '\n'.join(f'{x[0]} rolled {x[1]}' for x in rolls)
        await ctx.channel.send(results)
        
    @commands.command()
    async def choose(self, ctx, *options: str):
        if not await self.is_enabled(ctx.guild.id):
            return

        await ctx.channel.send(random.choice(options))
