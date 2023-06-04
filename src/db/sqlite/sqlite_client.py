import sqlite3
import logging

from ..base_client import BaseClient

class SqliteClient(BaseClient):
    def __init__(self, config):
        super().__init__()
        self.connection = sqlite3.connect(config['db']['sqlite']['path'], check_same_thread=False)
        self.__init_check_db(config['db']['sqlite'], config['categories'], config['flow_types'])

        self.insert_plan_query = config['db']['sqlite']['insert_plan']
        self.insert_flow_query = config['db']['sqlite']['insert_flow']
        self.update_plan_query = config['db']['sqlite']['update_plan']
        # self.update_flow = config['db']['sqlite']['update_flow']
        self.get_plan_by_chat_id = config['db']['sqlite']['select_plan_by_chat_id']
        self.select_categories = config['db']['sqlite']['select_categories']
        self.select_flow_types = config['db']['sqlite']['select_flow_types']

    def map_categories2ids(self, plan):
        category2id = {v[0] : v[1] for v in self.connection.execute(self.select_categories).fetchall()}
        for plan_item in plan:
            plan_item['category_id'] = category2id[plan_item['category_id']]

    def insert_plan(self, plan):
        self.map_categories2ids(plan)
        self.connection.executemany(self.insert_plan_query, plan)
        self.connection.commit()

    def update_plan(self, plan, need_map_cat=True):
        self.map_categories2ids(plan)
        self.connection.executemany(self.update_plan_query, plan)
        self.connection.commit()

    def map_flows2ids(self,flow):
        category2id = {v[0] : v[1] for v in self.connection.execute(self.select_flow_types).fetchall()}
        for flow_item in flow:
            flow_item['flow_type_id'] = category2id[flow_item['flow_type_id']]

    def insert_flow(self, flow):
        self.map_categories2ids(flow)
        self.map_flows2ids(flow)
        self.connection.executemany(self.insert_flow_query, flow)
        self.connection.commit()

    def select_plan_by_chat_id(self, id):
        result = self.connection.execute(self.get_plan_by_chat_id + str(id)).fetchall()
        return result

    def __init_check_db(self, config, categories, flow_types):
        # check all tables in database
        result = self.connection.execute(config['check_tables'] + ', '.join(['"' + table + '"' for table in config['tables']]) + ')').fetchall()
        if len(result) != len(config['tables']):
            logging.info('Creating tables')
            self.connection.executescript(config['create_tables'])

        # check all values in categories
        result = self.connection.execute(config['select_categories']).fetchall()
        if len(result) != len(categories):
            logging.info('Inserting categories!')
            result = [result_item[0] for result_item in result]
            to_insert_categories = [(category, ) for category in categories if category not in result]
            self.connection.executemany(config['insert_categories'], to_insert_categories)
            self.connection.commit()

        # check all values in flow_type
        result = self.connection.execute(config['select_flow_types']).fetchall()
        if len(result) != len(flow_types):
            logging.info('Inserting flow types!')
            result = [result_item[0] for result_item in result]
            to_insert_flow_types = [(flow_type, ) for flow_type in flow_types if flow_type not in result]
            self.connection.executemany(config['insert_flow_types'], to_insert_flow_types)
            self.connection.commit()
