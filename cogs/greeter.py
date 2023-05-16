import discord
from discord.ext import commands
from ..dictcache import DictCache
from .. import checks

class Greeter(commands.GroupCog, group_name='greeter'):
    def __init__(self, bot):
        self.bot = bot
        self.settings = DictCache()
    
    async def load_settings(self, guildid):
        if guildid in self.settings:
            return self.settings[guildid]

        storage = self.bot.get_cog('Storage')
        loadSettings = await storage.load_doc('greeter', f'settings:{guildid}')
        if loadSettings is None:
            loadSettings = {'welcome_channel': None, 'welcome_message': None, 'welcome_dm': None}
        self.settings[guildid] = loadSettings

        return loadSettings

    async def save_settings(self, guildid):
        storage = self.bot.get_cog('Storage')
        await storage.save_doc('greeter', f'settings:{guildid}', self.settings[guildid])

    async def is_enabled(self, guildid):
        settings = self.bot.get_cog('Settings')
        return await settings.is_cog_enabled(guildid, 'greeter')
    
    @commands.hybrid_command()
    async def set_welcome_channel(self, ctx, channel: discord.TextChannel):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        settings = await self.load_settings(ctx.guild.id)
        settings['welcome_channel'] = channel.id
        await self.save_settings(ctx.guild.id)
        await ctx.send(f'Welcome channel set to {channel}')

    @commands.hybrid_command()
    async def set_welcome_message(self, ctx, channel: discord.TextChannel, messageid):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        settings = await self.load_settings(ctx.guild.id)
        settings['welcome_message'] = {'channel': channel.id, 'msgid': messageid}
        await self.save_settings(ctx.guild.id)
        await ctx.send("Welcome message set")

    @commands.hybrid_command()
    async def set_welcome_dm(self, ctx, channel: discord.TextChannel, messageid):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        settings = await self.load_settings(ctx.guild.id)
        settings['welcome_dm'] = {'channel': channel.id, 'msgid': messageid}
        await self.save_settings(ctx.guild.id)
        await ctx.send("Welcome DM message set")

        
    @commands.hybrid_command()
    async def test_welcome(self, ctx):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        await self.on_member_join(ctx.author)
        
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not await self.is_enabled(member.guild.id):
            return
        settings = await self.load_settings(member.guild.id)
        welcome_channel = self.bot.get_channel(settings['welcome_channel'])
        msg_channel = self.bot.get_channel(settings['welcome_message']['channel'])
        welcome_message = await msg_channel.fetch_message(settings['welcome_message']['msgid'])
        dm_channel = self.bot.get_channel(settings['welcome_dm']['channel'])
        dm = await dm_channel.fetch_message(settings['welcome_dm']['msgid'])
        
        if welcome_channel is not None:
            files = [await a.to_file() for a in welcome_message.attachments]
            await welcome_channel.send(content = welcome_message.content.replace('<member>', member.mention), files=files)

            files = [await a.to_file() for a in dm.attachments]
            member_dm = await member.create_dm()
            await member_dm.send(content = dm.content, files = files)
            
    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def sync(self, ctx):
        if not await checks.is_admin(self.bot, ctx):
            return
        await self.bot.tree.sync()

