from discord.ext import commands

from dictcache import DictCache

class Settings(commands.GroupCog, group_name='settings'):
    def __init__(self, bot):
        self.bot = bot
        self.settings = DictCache()
        
    async def load_settings(self, guildid):
        if guildid in self.settings:
            return self.settings[guildid]

        storage = self.bot.get_cog('Storage')
        loadSettings = await storage.load_doc('settings', f'cogs:{guildid}')
        if loadSettings is None:
            loadSettings = {}
        self.settings[guildid] = loadSettings

        return loadSettings
    
    async def save_settings(self, guildid):
        storage = self.bot.get_cog('Storage')
        await storage.save_doc('settings', f'cogs:{guildid}', self.settings[guildid])
    
    @commands.hybrid_command()
    @commands.is_owner()
    async def enable_cog(self, ctx, cogname: str):
        settings = await self.load_settings(ctx.guild.id)
        settings[cogname] = True
        await self.save_settings(ctx.guild.id)
        await ctx.send(f'Enabled cog "{cogname}"')
    
    @commands.hybrid_command()
    @commands.is_owner()
    async def disable_cog(self, ctx, cogname: str):
        settings = await self.load_settings(ctx.guild.id)
        settings[cogname] = False
        await self.save_settings(ctx.guild.id)
        await ctx.send(f'Disabled cog "{cogname}"')

    async def is_cog_enabled(self, guildid: int, cogname: str):
        settings = await self.load_settings(guildid)
        if cogname in settings:
            return settings[cogname]
        return False

