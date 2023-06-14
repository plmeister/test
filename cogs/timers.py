from datetime import datetime, timezone
import asyncio
import discord
import re
from discord import Message
from discord.ext import commands
from discord.ext import tasks

from dictcache import DictCache
import checks

class Timer(commands.GroupCog, group_name='timer'):
    def __init__(self, bot):
        self.bot = bot
        self.settings = DictCache()
        self.timers = DictCache()

    async def load_settings(self, guildid):
        if guildid in self.settings:
            return self.settings[guildid]

        storage = self.bot.get_cog('Storage')
        loadSettings = await storage.load_doc('timer', f'settings:{guildid}')
        if loadSettings is None:
            loadSettings = {'channels': {}} #{'input_channel': None, 'output_channel': None, 'timeout': 3}
        self.settings[guildid] = loadSettings

        return loadSettings

    async def load_timers(self, guildid):
        storage = self.bot.get_cog('Storage')
        x = await storage.load_doc('timer', f'timers:{guildid}')
        if x is None:
            x = {'timers': {}}
        self.timers[guildid] = x
        return x
    
    async def save_timers(self, guildid, timers):
        storage = self.bot.get_cog('Storage')
        x = await storage.save_doc('timer', f'timers:{guildid}', timers)

    async def save_settings(self, guildid):
        storage = self.bot.get_cog('Storage')
        await storage.save_doc('timer', f'settings:{guildid}', self.settings[guildid])

    async def is_enabled(self, guildid):
        settings = self.bot.get_cog('Settings')
        return await settings.is_cog_enabled(guildid, 'timer')
    
    @commands.hybrid_command()
    async def countdown(self, ctx, member: discord.Member, description: str, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0):
        if not await self.is_enabled(ctx.guild.id):
            return
        #settings = await self.load_settings(ctx.guild.id)
        #settings['channels'][str(storage_channel.id)] = {'output_channel': output_channel.id, 'timeout': timeout}
        
        if (member != None):
            if not await checks.is_admin(self.bot, ctx):
                await ctx.send("You must be an admin to set a timer for someone else")
                return
        else:
            member = ctx.author

        totalseconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds
    
        all_timers = await self.load_timers(ctx.guild.id)
        key = str(member.id)
        if key in all_timers:
            member_timers = all_timers[str(member.id)]
        else:
            member_timers = []

        now = int(datetime.now(timezone.utc).timestamp())
        countdown = now + totalseconds

        member_timers.append({'type': 'countdown', 'created': now, 'timestamp': countdown, 'description': description, 'addedby': ctx.author.id})

        await self.save_timers(ctx.guild.id, all_timers)
        await ctx.send(f"Countdown '{description}' set for {member}, ending <t:{countdown}:R> \<t:{countdown}:R\> <t:{countdown}> \<t:{countdown}\>")

    @commands.hybrid_command()
    async def list(self, ctx, member: discord.Member = None):
        if not await self.is_enabled(ctx.guild.id):
            return
        all_timers = await self.load_timers(ctx.guild.id)
        if member == None:
            member = ctx.author
        await ctx.send

    @commands.hybrid_command()
    async def stopwatch(self, ctx):
        if not await self.is_enabled(ctx.guild.id):
            return
        
        await ctx.send(view=StopWatch().create(), embed=discord.Embed(title="Stopwatch", description="Get Ready..."))

class StopWatch:
    def __init__(self):
        self.start_button = StartButton(discord.ButtonStyle.green, self.onstart)
        self.stop_button = StopButton(discord.ButtonStyle.red, self.onstop)
        pass
    def create(self):
        self.view = discord.ui.View()
        
        self.view.add_item(self.start_button)
        self.view.add_item(self.stop_button)
        return self.view

    async def onstart(self, interaction):
        self.started = datetime.now(timezone.utc)
        self.stop_button.disabled = False
        await interaction.response.edit_message(view=self.view, embed=discord.Embed(title="Stopwatch", description="GO!"))

    async def onstop(self, interaction):
        self.stopped = datetime.now(timezone.utc)
        time = int((self.stopped - self.started).total_seconds())
        await interaction.response.edit_message(view=None, embed=None, content = f"Time was {time} seconds - {interaction.user.display_name}")



class StartButton(discord.ui.Button):
    def __init__(self, style: discord.ButtonStyle, callback):
        super().__init__(label="Start", style=style)
        self.oncallback = callback

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        await self.oncallback(interaction)
        
class StopButton(discord.ui.Button):
    def __init__(self, style: discord.ButtonStyle, callback):
        super().__init__(label="Stop", style=style)
        self.disabled = True
        self.oncallback = callback

    async def callback(self, interaction: discord.Interaction):
        await self.oncallback(interaction)
