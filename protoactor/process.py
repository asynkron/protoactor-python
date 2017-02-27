from abc import abstractmethod, ABCMeta
from asyncio import Task
from typing import Dict, Optional, Callable
from uuid import uuid4

from . import utils, invoker, message_sender, pid
from .mailbox import mailbox


class AbstractProcess(metaclass=ABCMeta):
    @abstractmethod
    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def send_system_message(self, pid: 'PID', message: object):
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def stop(self):
        raise NotImplementedError('Should implement this method')


class LocalProcess(AbstractProcess, invoker.AbstractInvoker):
    def __init__(self, mailbox: mailbox.AbstractMailbox) -> None:
        self.__mailbox = mailbox

    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        if sender:
            self.__mailbox.post_user_message(message_sender.MessageSender(message, sender))
        else:
            self.__mailbox.post_user_message(message)

    def send_system_message(self, pid: 'PID', message: object):
        self.__mailbox.post_system_message(message)

    def stop(self):
        raise NotImplementedError("Should Implement this method")

    def invoke_system_message(self, message: object) -> Task:
        raise NotImplementedError("Should Implement this method")

    def invoke_user_message(self, message: object) -> Task:
        pass

    def escalate_failure(self, reason: Exception, message: object):
        raise NotImplementedError("Should Implement this method")


class DeadLettersProcess(AbstractProcess):
    def stop(self):
        raise NotImplementedError("Should Implement this method")

    def send_system_message(self, pid: 'PID', message: object):
        EventStream().publish(DeadLetterEvent(pid, message, None))

    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        EventStream().publish(DeadLetterEvent(pid, message, sender))


class DeadLetterEvent:
    def __init__(self, pid: 'PID', message: object, sender: Optional['PID']) -> None:
        self.__pid = pid
        self.__message = message
        self.__sender = sender

    @property
    def pid(self) -> 'PID':
        return self.__pid

    @property
    def message(self) -> object:
        return self.__message

    @property
    def sender(self) -> Optional['PID']:
        return self.__sender


@utils.singleton
class EventStream:
    def __init__(self):
        self._subscriptions: Dict[uuid4, Callable[..., None]] = {}
        self.subscribe(self.__report_deadletters)

    def subscribe(self, fun: Callable[..., None]) -> None:
        uniq_id = uuid4()
        self._subscriptions[uniq_id] = fun

    def publish(self, message: object) -> None:
        for sub in self._subscriptions.values():
            sub(message)

    def __report_deadletters(self, message: DeadLetterEvent) -> None:
        if isinstance(message, DeadLetterEvent):
            console_message = """[DeadLetterEvent] %(pid)s got %(message_type)s:%(message)s from
            %(sender)s""" % {"pid": message.pid,
                             "message_type": type(message.message),
                             "message": message.message,
                             "sender": message.sender
                             }
            print(console_message)
