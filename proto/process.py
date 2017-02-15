from abc import abstractmethod, ABCMeta

from .pid import PID
from .mailbox.mailbox import AbstractMailbox
from .message_sender import MessageSender


class AbstractProcess(metaclass=ABCMeta):
    @abstractmethod
    def send_user_message(self, pid: PID , message: object, sender: PID =None):
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def send_system_message(self, pid: PID , message: object, sender: PID):
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def stop(self):
        raise NotImplementedError('Should implement this method')


class LocalProcess(AbstractProcess):
    def __init__(self, mailbox: AbstractMailbox):
        self.__mailbox = mailbox

    def send_user_message(self, pid: PID, message: object, sender: PID = None):
        if sender:
            self.__mailbox.post_user_message(MessageSender(message, sender))
        else:
            self.__mailbox.post_user_message(message)

    def send_system_message(self, pid: PID, message: object, sender: PID):
        pass

    def stop(self):
        pass


