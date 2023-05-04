from discord.ext import commands
import discord
from table2ascii import table2ascii as t2a, PresetStyle

class Scores(commands.GroupCog, group_name='scores'):
    def __init__(self, bot):
        self.bot = bot
        self.settings = {}
        self.data = {}

    async def load_settings(self, guildid):
        if guildid in self.settings:
            return self.settings[guildid]

        storage = self.bot.get_cog('Storage')
        loadSettings = await storage.load_doc('scores', f'settings:{guildid}')
        if loadSettings is None:
            loadSettings = {'boards': {} }
        self.settings[guildid] = loadSettings

        return loadSettings

    async def save_settings(self, guildid):
        storage = self.bot.get_cog('Storage')
        await storage.save_doc('scores', f'settings:{guildid}', self.settings[guildid])

    async def is_enabled(self, guildid):
        settings = self.bot.get_cog('Settings')
        return await settings.is_cog_enabled(guildid, 'Scores')

    async def get_data(self, guildid, user):
        if guildid in self.data:
            if user in self.data[guildid]:
                return self.data[guildid][user]
        else:
            self.data[guildid] = {}
        current_xp = await self.get_xp(guildid, user)
        self.data[guildid][user] = current_xp
        return current_xp

    @commands.hybrid_command()
    @commands.is_owner()
    async def create_race_board(self, ctx, name: str, max: int = 10):
        if not await self.is_enabled(ctx.guild.id):
            return
        settings = await self.load_settings(ctx.guild.id)
        if name not in settings['boards']:
            settings['boards'][name] = {'type': 'race', 'max': max, 'entries': {}}
            await self.save_settings(ctx.guild.id)
            await ctx.send(f"Race Scoreboard '{name}' created")
    
    @commands.hybrid_command()
    @commands.is_owner()
    async def create_endurance_board(self, ctx, name: str):
        if not await self.is_enabled(ctx.guild.id):
            return
        settings = await self.load_settings(ctx.guild.id)
        if name not in settings['boards']:
            settings['boards'][name] = {'type': 'endurance', 'entries': {}}
            await self.save_settings(ctx.guild.id)
            await ctx.send(f"Endurance Scoreboard '{name}' created")
    
    @commands.hybrid_command()
    async def show_board(self, ctx, name: str):
        if not await self.is_enabled(ctx.guild.id):
            return
        settings = await self.load_settings(ctx.guild.id)
        if name not in settings['boards']:
            await ctx.send(f"Scoreboard '{name}' not found")
            return
        board = settings['boards'][name]
        
        sortedScores = []
        if board['type'] == 'race': # lowest entries at the top
            sortedScores = list(sorted(board['entries'].items(), key=lambda item: item[1]))
        elif board['type'] == 'endurance':
            sortedScores = list(sorted(board['entries'].items(), key=lambda item: item[1]))

        data = []
        for count, item in enumerate(sortedScores):
            data.append([count + 1, item[0], item[1]])

        output = t2a(header=["Rank", "Name", "Score"], body=data, style=PresetStyle.thin_compact)
        
        await ctx.send(f"```\n{output}\n```")

    @commands.hybrid_command()
    async def post_time(self, ctx, name: str, seconds: int):
        if not await self.is_enabled(ctx.guild.id):
            return
        settings = await self.load_settings(ctx.guild.id)
        if name not in settings['boards']:
            await ctx.send(f"Scoreboard '{name}' not found")
            return
        settings['boards'][name]['entries'][str(ctx.author)] = seconds
        await self.save_settings(ctx.guild.id)
        await ctx.send(f"Recorded time of {seconds} seconds for {str(ctx.author)} on scoreboard '{name}'")



