from ..redis.redis_cache_client import RedisCacheClient

CACHE_CLIENT_MAPPING = {
    'redis': RedisCacheClient
}


def get_client_by_config(config):
    if config['type'] in CACHE_CLIENT_MAPPING:
        return CACHE_CLIENT_MAPPING[config['type']](config[config['type']])
    raise NotImplementedError(f'CacheClient of type {config["type"]} is not implemented')
