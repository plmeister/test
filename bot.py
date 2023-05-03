import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from cogs.dice import Dice
from cogs.greeter import Greeter
from cogs.settings import Settings
from cogs.image_reactions import ImgReact
from cogs.storage import Storage
from cogs.xp import XP
from cogs.scores import Scores
from cogs.count import Count

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True
intents.message_content = True
intents.reactions = True

class MyBot(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

async def configure(bot):
    await bot.add_cog(Storage(bot, 'botpy'))
    await bot.add_cog(Settings(bot))
    await bot.add_cog(XP(bot))
    await bot.add_cog(Dice(bot))
    await bot.add_cog(Greeter(bot))
    await bot.add_cog(ImgReact(bot))
    await bot.add_cog(Scores(bot))
    await bot.add_cog(Count(bot))

if __name__ == "__main__":
    import asyncio
    bot = MyBot(command_prefix='!', intents=intents)
    
    asyncio.run(configure(bot))

    bot.run(TOKEN)

