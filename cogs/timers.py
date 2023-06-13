from datetime import datetime, timezone
import asyncio
import discord
import re
from discord import Message
from discord.ext import commands
from discord.ext import tasks

from dictcache import DictCache
import checks

class Timer(commands.GroupCog, group_name='timers'):
    def __init__(self, bot):
        self.bot = bot
        self.settings = DictCache()

    async def load_settings(self, guildid):
        if guildid in self.settings:
            return self.settings[guildid]

        storage = self.bot.get_cog('Storage')
        loadSettings = await storage.load_doc('timer', f'settings:{guildid}')
        if loadSettings is None:
            loadSettings = {'channels': {}} #{'input_channel': None, 'output_channel': None, 'timeout': 3}
        self.settings[guildid] = loadSettings

        return loadSettings

    async def save_settings(self, guildid):
        storage = self.bot.get_cog('Storage')
        await storage.save_doc('timer', f'settings:{guildid}', self.settings[guildid])

    async def is_enabled(self, guildid):
        settings = self.bot.get_cog('Settings')
        return await settings.is_cog_enabled(guildid, 'timer')
    
    @commands.hybrid_command()
    async def countdown(self, ctx, member: discord.Member, duration: str, description: str):
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
        
        inputSplit = re.split('(\d+)', duration)
        del inputSplit[0]

        seconds = 0

        #  Looping through inputSplit, from first to last letter
        for i in range(1, len(inputSplit),2):
            timeModifier = inputSplit[i]     # Modifier is the letter
            timeValue = int(inputSplit[i-1]) # Value is number before modifier

            # Same if loop as yours. Checking modifiers and adding the value
            if timeModifier == "d":
                seconds += 86400 * timeValue
            elif timeModifier == "h":
                seconds += 3600 * timeValue
            elif timeModifier == "m":
                seconds += 60 * timeValue
            elif timeModifier == "s":
                seconds += timeValue
            
        current_timers = await self.load_timers(ctx.guild.id, member)
        now = datetime.now(timezone.utc)

        current_timers.append({})

        await self.save_settings(ctx.guild.id)
        await ctx.send('Done')

    @commands.hybrid_command()
    async def remove(self, ctx, storage_channel: discord.TextChannel):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        settings = await self.load_settings(ctx.guild.id)
        del settings['channels']
        await self.save_settings(ctx.guild.id)
        await ctx.send('Done')

