import datetime
from sys import set_coroutine_origin_tracking_depth

class CacheItem:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.timestamp = datetime.datetime.now()
    def update(self, value):
        self.value = value
        self.timestamp = datetime.datetime.now()


class DictCache:
    def __init__(self, capacity=128):
        self.storage = {}
        self.capacity = capacity
        self.index = []

    def __contains__(self, key):
        return key in self.storage

    def __getitem__(self, key):
        if key in self.storage:
            return self.storage[key].value
        return None

    def __setitem__(self, key, value):
        if key in self.storage:
            cacheitem = self.storage[key]
            self.index.remove(cacheitem)
            self.storage[key].update(value)
            self.index.append(cacheitem)
            if len(self.index) > self.capacity:
                self.evict(self.index[0])
        else:
            cacheitem = CacheItem(key, value)
            self.storage[key] = cacheitem
            self.index.append(cacheitem)
            
    def evict(self, key):
        if key in self.storage:
            cacheitem = self.storage[key]
            del self.storage[key]
            self.index.remove(cacheitem)

