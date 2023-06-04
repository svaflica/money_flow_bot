import redis

from ..utils.serialize import serialize_value, deserialize_value
from ..base_cache_client import BaseCacheClient

class RedisCacheClient(BaseCacheClient):
    def __init__(self, config):
        self.host = config['host']
        self.port = config['port']
        self.db = config.get('db', 0)
        self.expire_time = config.get('expire_time', 60 * 60 * 24)
        self.health_check_interval = config.get('health_check_interval', 3600)
        self.socket_timeout = config.get('socket_timeout', 5)
        self.client = None

    def get(self, key):
        try:
            if self.client is None:
                self.client = self.__connect()
            return deserialize_value(self.client.get(key))
        except:
            return None

    def set(self, key, value):
        try:
            if self.client is None:
                self.client = self.__connect()
            self.client.set(key, serialize_value(value), self.expire_time)
        except:
            return

    def delete(self, key):
        try:
            if self.client is None:
                self.client = self.__connect()
            self.client.delete(key)
        except:
            return

    def __connect(self):
        return redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    socket_timeout=self.socket_timeout,
                    health_check_interval=self.health_check_interval
                )
