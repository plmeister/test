﻿from discord.ext import commands
import discord
import random

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = {}
        self.data = {}

    async def load_settings(self, guildid):
        if guildid in self.settings:
            return self.settings[guildid]

        storage = self.bot.get_cog('Storage')
        loadSettings = await storage.load_doc('xp', f'settings:{guildid}')
        if loadSettings is None:
            loadSettings = {'levels': [] }
        self.settings[guildid] = loadSettings

        return loadSettings

    async def save_settings(self, guildid):
        storage = self.bot.get_cog('Storage')
        await storage.save_doc('xp', f'settings:{guildid}', self.settings[guildid])

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
    async def set_xp(self, ctx, user: discord.Member, xp: int):
        current_xp = await self.get_data(ctx.guild.id, user)
        await self.add_xp(ctx.guild, user, xp - current_xp)
    
    async def add_xp(self, guild, user, value):
        storage = self.bot.get_cog('Storage')
        settings = await self.load_settings(guild.id)
        current_xp = await self.get_data(guild.id, user)
        current_xp += value
        self.data[guild.id][user] = current_xp
        await storage.set_value('xp', f'{guild.id}:{user}', current_xp)
       
        allowedRoles = list(filter(lambda x: x['level'] <= current_xp, settings['levels']))
        disallowedRoles = list(filter(lambda x: x['level'] > current_xp, settings['levels']))
        currentUserRoles = list(map(lambda x: x.id, filter(lambda x: x.id, user.roles)))
        
        rolesToAdd = []
        for role in filter(lambda x: x['role'] not in currentUserRoles, allowedRoles):
            rolesToAdd.append(role['role'])

        rolesToRemove = []
        for role in filter(lambda x: x['role'] in currentUserRoles, disallowedRoles):
            rolesToRemove.append(role['role'])

        for r in rolesToAdd:
            await user.add_roles(discord.Object(r))

        for r in rolesToRemove:
            await user.remove_roles(discord.Object(r))

    async def get_xp(self, guildid, user):
        storage = self.bot.get_cog('Storage')
        current_xp = await storage.get_value('xp', f'{guildid}:{user}', 0)
        return current_xp

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        if len(msg.attachments) > 0:
            await self.add_xp(msg.guild, msg.author, 3)
        else:
            await self.add_xp(msg.guild, msg.author, 1)

    @commands.hybrid_command()
    async def xp(self, ctx):
        current_xp = await self.get_data(ctx.guild.id, ctx.author)
        await ctx.reply(f'You currently have {current_xp} XP')

    @commands.hybrid_command()
    @commands.is_owner()
    async def set_level(self, ctx, level: int, role: discord.Role):
        settings = await self.load_settings(ctx.guild.id)
        settings['levels'] = list(filter(lambda a: a['role'] != role.id, settings['levels']))
        settings['levels'].append({'role': role.id, 'level': level})
        await self.save_settings(ctx.guild.id)
        await ctx.send("done")
        
    @commands.hybrid_command()
    async def show_levels(self, ctx):
        settings = await self.load_settings(ctx.guild.id)
        msg = ''
        for lvl in sorted(settings['levels'], key = lambda x: x['level']):
            msg += f'{lvl["level"]} - {lvl["role"]}\n'
        if msg == '':
            await ctx.send('No levels configured')
        else:
            await ctx.send(msg)

    @commands.hybrid_command()
    @commands.is_owner()
    async def del_level(self, ctx, role: discord.Role):
        settings = await self.load_settings(ctx.guild.id)
        settings['levels'] = filter(lambda a: a['role'] != role.id, settings['levels'])
        await self.save_settings(ctx.guild.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        msgid = payload.message_id
        chid = payload.channel_id
        guildid = payload.guild_id

        ch = self.bot.get_channel(chid)
        msg = await ch.fetch_message(msgid)
            
        if payload.member.guild.owner.id == payload.member.id:
            if payload.emoji.name == '💯':
                await self.add_xp(msg.guild, msg.author, 100)
