from abc import ABCMeta, abstractmethod
from enum import Enum


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
    def register_handlers(self, invoker, dispatcher):
        pass

    def post_system_message(self, msg):
        pass

    def post_user_message(self, msg):
        pass

    def start(self):
        pass