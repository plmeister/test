from discord.ext import commands
import discord
from dictcache import DictCache
from table2ascii import table2ascii as t2a, PresetStyle
import checks
from datetime import datetime, timezone

class XP(commands.GroupCog, group_name='xp'):
    def __init__(self, bot):
        self.bot = bot
        self.settings = DictCache()
        self.data = DictCache()
        
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
        
    async def is_enabled(self, guildid):
        settings = self.bot.get_cog('Settings')
        return await settings.is_cog_enabled(guildid, 'xp')
    
    async def get_data(self, guildid, user):
        if guildid in self.data:
            if str(user.id) in self.data[guildid]:
                return self.data[guildid][str(user.id)]
        else:
            self.data[guildid] = {}
        current_xp = await self.get_xp(guildid, user)
        self.data[guildid][str(user.id)] = current_xp
        return current_xp

    @commands.hybrid_command()
    async def set_xp(self, ctx, user: discord.Member, xp: int):
        if not await self.is_enabled(ctx.guild.id):
            return        
        if not await checks.is_admin(self.bot, ctx):
            return

        current_xp = await self.get_data(ctx.guild.id, user)
        await self.add_xp(ctx.guild, user, xp - current_xp['xp'])
    
    @commands.hybrid_command()
    async def set_xp_for_role(self, ctx, role: discord.Role, xp: int):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return

        affected = 0
        for m in role.members:
            current_xp = await self.get_data(ctx.guild.id, m)
            if (current_xp != 0):
                await self.add_xp(ctx.guild, m, xp - current_xp['xp'])
                affected += 1
        await ctx.send(f'Affected {affected} members')

    @commands.hybrid_command()
    async def adjust(self, ctx, role: discord.Role, percent: int):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        affected = 0
        for m in role.members:
            current_xp = await self.get_data(ctx.guild.id, m)
            if (current_xp != 0):
                new_xp = int((current_xp * percent) / 100)
                await self.add_xp(ctx.guild, m, new_xp - current_xp['xp'])
                affected += 1
        await ctx.send(f'Affected {affected} members')

    @commands.hybrid_command()
    async def boost(self, ctx, role: discord.Role, amount: int):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        affected = 0
        for m in role.members:
            current_xp = await self.get_data(ctx.guild.id, m)
            if (current_xp != 0):
                await self.add_xp(ctx.guild, m, amount)
                affected += 1
        await ctx.send(f'Affected {affected} members')

    @commands.hybrid_command()
    async def leaderboard(self, ctx, role: discord.Role, limit: int = 10, page: int = 1):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        
        data = []
        for m in role.members:
            current_xp = await self.get_data(ctx.guild.id, m)
            if (current_xp['xp'] != 0):
                data.append([m.display_name, current_xp['xp']])
        data = sorted(data, key = lambda x: -x[1])
        d2 = []
        prev = None
        for i,d in enumerate(data):
            if d[1] != prev:
                place,prev = i+1,d[1]
            d2.append([place, d[0][:15], d[1]])
        page_counter = 1
        while d2 != []:
            paged_data, d2 = d2[:limit], d2[limit:]
            output = t2a(header=["Rank", "Member", "XP"], body=paged_data, style=PresetStyle.thin_compact)
            await ctx.channel.send(f'```\n{output}\n(page {page_counter})```')
            page_counter += 1

    @commands.hybrid_command()
    async def kick_role(self, ctx, role: discord.Role):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        
        for m in role.members:
            if not m.bot: # don't kick bots
                if not await checks.is_admin(self.bot, ctx): # don't kick admins
                    await ctx.guild.kick(m)
                    await ctx.channel.send(f"User {m} has been kicked")

    @commands.hybrid_command()
    async def show_inactive(self, ctx, role: discord.Role, days_inactive: int, limit: int = 10, page: int = 1):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        
        timenow = int(datetime.now(timezone.utc).timestamp())
        seconds_inactive = days_inactive * 86400

        data = []
        for m in role.members:
            current_xp = await self.get_data(ctx.guild.id, m)
            if timenow - current_xp['activity'] > seconds_inactive:
                last_active = datetime.utcfromtimestamp(current_xp['activity'])
                data.append([m.display_name, current_xp['xp'], last_active.isoformat()])

        data = sorted(data, key = lambda x: -x[1])
        d2 = []
        prev = None
        for i,d in enumerate(data):
            d2.append([d[0][:15], d[1], d[2]])
        page_counter = 1
        while d2 != []:
            paged_data, d2 = d2[:limit], d2[limit:]
            output = t2a(header=["Member", "XP", "Last Active"], body=paged_data, style=PresetStyle.thin_compact)
            await ctx.channel.send(f'```\n{output}\n(page {page_counter})```')
            page_counter += 1

    @commands.hybrid_command()
    async def mark_inactive(self, ctx, role: discord.Role, add_to_role: discord.Role, days_inactive: int):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        timenow = int(datetime.now(timezone.utc).timestamp())
        seconds_inactive = days_inactive * 86400
        for m in role.members:
            current_xp = await self.get_data(ctx.guild.id, m)
            if timenow - current_xp['activity'] > seconds_inactive:
                await m.add_roles(add_to_role)
            else:
                await m.remove_roles(add_to_role)

    async def add_xp(self, guild, user, value: int, mark_activity: bool = False):
        storage = self.bot.get_cog('Storage')
        settings = await self.load_settings(guild.id)
        current_xp = await self.get_data(guild.id, user)
        current_xp['xp'] += value
        if mark_activity:
            current_xp['activity'] = int(datetime.now(timezone.utc).timestamp())
        self.data[guild.id][str(user.id)] = current_xp
        await storage.set_value('xp', f'{guild.id}:{str(user.id)}', current_xp)
       
        allowedRoles = list(filter(lambda x: x['level'] <= current_xp['xp'], settings['levels']))
        disallowedRoles = list(filter(lambda x: x['level'] > current_xp['xp'], settings['levels']))
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
        current_xp = await storage.get_value('xp', f'{guildid}:{str(user.id)}', {'null': True})
        if current_xp == {'null': True}:
            current_xp = await storage.get_value('xp', f'{guildid}:{user}', 0)
        if not (type(current_xp) is dict):
            current_xp = {'xp': current_xp, 'activity': 0, 'name': user.name}
        
        return current_xp

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        if not await self.is_enabled(msg.guild.id):
            return
        if len(msg.attachments) > 0:
            await self.add_xp(msg.guild, msg.author, 2, True)
        else:
            await self.add_xp(msg.guild, msg.author, 1, True)

    @commands.hybrid_command()
    async def check(self, ctx):
        if not await self.is_enabled(ctx.guild.id):
            return
        current_xp = await self.get_data(ctx.guild.id, ctx.author)
        await self.add_xp(ctx.guild, ctx.author, -10)
        await ctx.reply(f'You currently have {current_xp["xp"]} XP... oh no actually - check that again..')

    @commands.hybrid_command()
    async def set_level(self, ctx, level: int, role: discord.Role):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return
        settings = await self.load_settings(ctx.guild.id)
        settings['levels'] = list(filter(lambda a: a['role'] != role.id, settings['levels']))
        settings['levels'].append({'role': role.id, 'level': level})
        await self.save_settings(ctx.guild.id)
        await ctx.send("done")
        
    @commands.hybrid_command()
    async def show_levels(self, ctx):
        if not await self.is_enabled(ctx.guild.id):
            return
        settings = await self.load_settings(ctx.guild.id)
        data = []
        for lvl in sorted(settings['levels'], key = lambda x: x['level']):
            role = ctx.guild.get_role(lvl['role'])
            data.append([lvl["level"], role])
        if data == []:
            await ctx.send('No levels configured')
        else:
            output = t2a(header=["Level", "Role"], body=data, style=PresetStyle.thin_compact)
            await ctx.send(f"```\n{output}\n```")

    @commands.hybrid_command()
    async def del_level(self, ctx, role: discord.Role):
        if not await self.is_enabled(ctx.guild.id):
            return
        if not await checks.is_admin(self.bot, ctx):
            return

        settings = await self.load_settings(ctx.guild.id)
        settings['levels'] = list(filter(lambda a: a['role'] != role.id, settings['levels']))
        await self.save_settings(ctx.guild.id)
        await ctx.send("done")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not await self.is_enabled(payload.guild_id):
            return
        msgid = payload.message_id
        chid = payload.channel_id

        ch = self.bot.get_channel(chid)
        msg = await ch.fetch_message(msgid)
            
        if payload.member.guild.owner.id == payload.member.id:
            if payload.emoji.name == '💯':
                await self.add_xp(msg.guild, msg.author, 10)
                
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not await self.is_enabled(payload.guild_id):
            return
        msgid = payload.message_id
        chid = payload.channel_id

        ch = self.bot.get_channel(chid)
        msg = await ch.fetch_message(msgid)
            
        if payload.member.guild.owner.id == payload.member.id:
            if payload.emoji.name == '💯':
                await self.add_xp(msg.guild, msg.author, -10)

