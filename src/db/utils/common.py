from ..sqlite.sqlite_client import SqliteClient

DB_CLIENT_MAPPING = {
    'sqlite': SqliteClient
}


def get_db_client_by_config(config):
    if config['db']['type'] in DB_CLIENT_MAPPING:
        return DB_CLIENT_MAPPING[config['db']['type']](config)
    raise NotImplementedError(f'DBClient of type {config["db"]["type"]} is not implemented')
