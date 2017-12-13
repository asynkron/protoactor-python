from abc import abstractmethod, ABCMeta
from typing import Optional, Callable
from uuid import uuid4

from . import utils, message_sender, messages
from .mailbox import mailbox


class AbstractProcess(metaclass=ABCMeta):
    @abstractmethod
    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def send_system_message(self, pid: 'PID', message: object):
        raise NotImplementedError('Should implement this method')

    def stop(self, pid: 'PID') -> None:
        self.send_system_message(pid, messages.Stop())


class LocalProcess(AbstractProcess):
    def __init__(self, mailbox: mailbox.AbstractMailbox) -> None:
        self.__mailbox = mailbox
        self.__is_dead = false

    @property
    def mailbox(self) -> mailbox.AbstractMailbox:
        return self.__mailbox

    def setis_dead(self, value):
        __is_dead = value
    
    def getis_dead(self):
        return __is_dead

    is_dead = property(getis_dead, setis_dead)

    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        if sender:
            self.__mailbox.post_user_message(message_sender.MessageSender(message, sender))
        else:
            self.__mailbox.post_user_message(message)

    def send_system_message(self, pid: 'PID', message: object):
        self.__mailbox.post_system_message(message)


class DeadLettersProcess(AbstractProcess):
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
        self._subscriptions = {}
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
