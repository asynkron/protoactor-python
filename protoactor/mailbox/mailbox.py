from abc import ABCMeta, abstractmethod
from enum import Enum

from .queue import AbstractQueue


class MailBoxStatus(Enum):
    idle = 0
    busy = 1


class AbstractMailbox(metaclass=ABCMeta):
    @abstractmethod
    def post_user_message(self, msg):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def post_system_message(self, msg):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def register_handlers(self, invoker, dispatcher):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def start(self):
        raise NotImplementedError("Should Implement this method")

class Mailbox(AbstractMailbox):

    def __init__(self, system_messages_queue: AbstractQueue, user_messages_queue: AbstractQueue):
        self.__system_messages_queue = system_messages_queue
        self.__user_messages_queue = user_messages_queue

    def register_handlers(self, invoker, dispatcher):
        raise NotImplementedError("Should Implement this method")

    def post_system_message(self, msg):
        raise NotImplementedError("Should Implement this method")

    def post_user_message(self, msg):
        raise NotImplementedError("Should Implement this method")

    def start(self):
        raise NotImplementedError("Should Implement this method")