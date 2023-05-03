from discord.ext import commands
import os
import motor.motor_asyncio


class Storage(commands.Cog):
    def __init__(self, bot, dbname):
        self.bot = bot
        self.dbname = dbname
        
        uri = os.getenv("MONGO_CONNECTION")
        # Create a new client and connect to the server
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[dbname]
        
    
    async def set_value(self, collection: str, key: str, value):
        coll = self.db[collection]
        data = {'_id': key, 'value': value}
        await coll.update_one({'_id': key}, { '$set': {'value': value}}, upsert=True)

    async def get_value(self, collection: str, key: str, defaultValue=None):
        coll = self.db[collection]
        try:
            data = await coll.find_one(key)
            if data:
                return data['value']
        except Exception:
            pass
        return defaultValue

    async def load_doc(self, collection:str, key:str):
        coll = self.db[collection]
        try:
            data = await coll.find_one(key)
            return data
        except Exception:
            pass
        return {}

    async def save_doc(self, collection: str, key: str, data):
        coll = self.db[collection]
        await coll.update_one({'_id': key}, {'$set': data}, upsert=True)