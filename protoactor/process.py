from abc import abstractmethod, ABCMeta
from asyncio import Task

from .invoker import AbstractInvoker
from .mailbox.mailbox import AbstractMailbox
from .message_sender import MessageSender
from .pid import PID


class AbstractProcess(metaclass=ABCMeta):
    @abstractmethod
    def send_user_message(self, pid: PID , message: object, sender: PID =None):
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def send_system_message(self, pid: PID , message: object):
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def stop(self):
        raise NotImplementedError('Should implement this method')


class LocalProcess(AbstractProcess, AbstractInvoker):
    def __init__(self, mailbox: AbstractMailbox):
        self.__mailbox = mailbox

    def send_user_message(self, pid: PID, message: object, sender: PID = None):
        if sender:
            self.__mailbox.post_user_message(MessageSender(message, sender))
        else:
            self.__mailbox.post_user_message(message)

    def send_system_message(self, pid: PID, message: object):
        self.__mailbox.post_system_message(message)

    def stop(self):
        raise NotImplementedError("Should Implement this method")

    def invoke_system_message(self, message: object) -> Task:
        raise NotImplementedError("Should Implement this method")

    def escalate_failure(self, reason: Exception, message: object):
        raise NotImplementedError("Should Implement this method")

class DeadLettersProcess(AbstractProcess):
    pass

