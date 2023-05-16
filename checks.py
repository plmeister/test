import discord
from discord.ext import commands

async def is_admin(bot, ctx):   
    if not ctx.guild:
        raise discord.NoPrivateMessage
        
    if ctx.author.guild_permissions.administrator == True:
        return True
        
    settings = bot.get_cog('Settings')
    admin_role = await settings.load_admin_role(ctx.guild.id)
    
    if admin_role is not None:
        role = discord.utils.get(ctx.author.roles, id=admin_role)
        if role is None:
            return False
        return True

    return False
