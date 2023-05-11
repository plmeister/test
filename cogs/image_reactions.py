import asyncio
import discord
from discord import Message
from discord.ext import commands
from discord.ext import tasks

from dictcache import DictCache

class ImgReact(commands.GroupCog, group_name='imgreact'):
    def __init__(self, bot):
        self.bot = bot
        self.settings = DictCache()

    async def load_settings(self, guildid):
        if guildid in self.settings:
            return self.settings[guildid]

        storage = self.bot.get_cog('Storage')
        loadSettings = await storage.load_doc('imgreact', f'settings:{guildid}')
        if loadSettings is None:
            loadSettings = {'channels': {}} #{'input_channel': None, 'output_channel': None, 'timeout': 3}
        self.settings[guildid] = loadSettings

        return loadSettings

    async def save_settings(self, guildid):
        storage = self.bot.get_cog('Storage')
        await storage.save_doc('imgreact', f'settings:{guildid}', self.settings[guildid])

    async def is_enabled(self, guildid):
        settings = self.bot.get_cog('Settings')
        return await settings.is_cog_enabled(guildid, 'imgreact')
    
    @commands.hybrid_command()
    @commands.is_owner()
    async def setup(self, ctx, storage_channel: discord.TextChannel, output_channel: discord.TextChannel, timeout: int):
        if not self.is_enabled():
            return
        settings = await self.load_settings(ctx.guild.id)
        settings['channels'][storage_channel.id] = {'output_channel': output_channel.id, 'timeout': timeout}
        await self.save_settings(ctx.guild.id)
        await ctx.send('Done')

    @commands.hybrid_command()
    @commands.is_owner()
    async def remove(self, ctx, storage_channel: discord.TextChannel):
        if not self.is_enabled():
            return
        settings = await self.load_settings(ctx.guild.id)
        del settings['channels']
        await self.save_settings(ctx.guild.id)
        await ctx.send('Done')

    @commands.hybrid_command()
    @commands.is_owner()
    async def set_timeout(self, ctx, storage_channel: discord.TextChannel, timeout: int):
        if not self.is_enabled():
            return
        settings = await self.load_settings(ctx.guild.id)
        
        channels = settings['channels']
        if storage_channel.id not in channels:
            await ctx.send(f"Channel {storage_channel} is not set up as a storage channel")
            return

        thischan = channels[storage_channel.id]
        thischan['timeout'] = timeout

        await self.save_settings(ctx.guild.id)
        await ctx.send(f'Timeout set to {timeout} seconds')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not self.is_enabled():
            return
        settings = await self.load_settings(payload.guild_id)

        channels = settings['channels']
        if payload.channel_id not in channels:
            return

        thischan = channels[payload.channel_id]
        
        output_channel = thischan['output_channel']
        timeout = thischan['timeout']
        
        if output_channel is None:
            return
        
        ch = self.bot.get_channel(payload.channel_id)
        output = self.bot.get_channel(output_channel)

        msg = await ch.fetch_message(payload.message_id)
        
        if len(msg.attachments) == 1:
            f = await msg.attachments[0].to_file()
            await output.send(file=f, delete_after=timeout)

        elif len(msg.attachments) == 2:
            f1 = await msg.attachments[0].to_file()
            f2 = await msg.attachments[1].to_file()
            m = await output.send(file=f1)
            await asyncio.sleep(timeout)
            await m.edit(attachments=[f2])
                
