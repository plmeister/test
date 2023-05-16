from discord.ext import commands
import discord
from ..dictcache import DictCache
from .. import checks

class Settings(commands.GroupCog, group_name='settings'):
    def __init__(self, bot):
        self.bot = bot
        self.settings = DictCache()
        self.roles = DictCache()
        
    async def load_settings(self, guildid):
        if guildid in self.settings:
            return self.settings[guildid]

        storage = self.bot.get_cog('Storage')
        loadSettings = await storage.load_doc('settings', f'cogs:{guildid}')
        if loadSettings is None:
            loadSettings = {}
        self.settings[guildid] = loadSettings

        return loadSettings
    
    async def load_admin_role(self, guildid):
        if guildid in self.roles:
            return self.roles[guildid]

        storage = self.bot.get_cog('Storage')
        s = await storage.load_doc('settings', f'admin_role:{guildid}')
        if s is not None:
            self.roles[guildid] = s['roleid']
            return s
        return None

    async def save_admin_role(self, guildid, roleid):
        self.roles[guildid] = roleid
        storage = self.bot.get_cog('Storage')
        await storage.save_doc('settings', f'admin_role:{guildid}', {'roleid': self.roles[guildid]})

    async def save_settings(self, guildid):
        storage = self.bot.get_cog('Storage')
        await storage.save_doc('settings', f'cogs:{guildid}', self.settings[guildid])
    
    @commands.hybrid_command()
    async def enable_cog(self, ctx, cogname: str):
        if not await checks.is_admin(self.bot, ctx):
            return
        settings = await self.load_settings(ctx.guild.id)
        settings[cogname] = True
        await self.save_settings(ctx.guild.id)
        await ctx.send(f'Enabled cog "{cogname}"')
    
    @commands.hybrid_command()
    async def disable_cog(self, ctx, cogname: str):
        if not await checks.is_admin(self.bot, ctx):
            return
        settings = await self.load_settings(ctx.guild.id)
        settings[cogname] = False
        await self.save_settings(ctx.guild.id)
        await ctx.send(f'Disabled cog "{cogname}"')

    async def is_cog_enabled(self, guildid: int, cogname: str):
        settings = await self.load_settings(guildid)
        if cogname in settings:
            return settings[cogname]
        return False

    @commands.hybrid_command()
    async def set_admin_role(self, ctx, role: discord.Role):
        if not await checks.is_admin(self.bot, ctx):
            return
        await self.save_admin_role(ctx.guild.id, role.id)
        await ctx.send(f'Admin role set to {role}')