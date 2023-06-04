import telebot

from cache.utils.common import get_client_by_config
from db.utils.common import get_db_client_by_config


class BaseBot:
    def __init__(self, config):
        self.bot = telebot.TeleBot(config['bot']['id'])
        self.cache = get_client_by_config(config['cache'])
        self.db = get_db_client_by_config(config)
        self.functions = config['functions']
        self.max_errors = config['operations']['max_errors']
        self.categories = config['categories']
        self.flow_types = config['flow_types']
