from abc import ABC, abstractmethod


class BaseClient(ABC):
    @abstractmethod
    def insert_plan(self, plan):
        pass

    @abstractmethod
    def update_plan(self, plan):
        pass

    @abstractmethod
    def select_plan_by_chat_id(self, id):
        pass