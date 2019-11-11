from abc import ABCMeta
from typing import Optional

from protoactor.actor.protos_pb2 import PID
from protoactor.actor.restart_statistics import RestartStatistics
from protoactor.actor.utils import Singleton


class AbstractSystemMessage():
    pass

class AbstractNotInfluenceReceiveTimeout(metaclass=ABCMeta):
    pass

class AutoReceiveMessage(metaclass=ABCMeta):
    pass


class Restarting(metaclass=Singleton):
    pass


class Restart(AbstractSystemMessage):
    def __init__(self, reason):
        self.reason = reason


class Failure(AbstractSystemMessage):
    def __init__(self, who: PID, reason: Exception, crs: RestartStatistics) -> None:
        self.__who = who
        self.__reason = reason
        self.__crs = crs

    @property
    def who(self) -> PID:
        return self.__who

    @property
    def reason(self) -> Exception:
        return self.__reason

    @property
    def restart_statistics(self) -> RestartStatistics:
        return self.__crs


class SystemMessage:
    pass


class Stopping(AutoReceiveMessage):
    pass


class Stopped(AutoReceiveMessage):
    pass


class Started(AbstractSystemMessage):
    pass


class ReceiveTimeout(AbstractSystemMessage, metaclass=Singleton):
    pass


class NotInfluenceReceiveTimeout(AbstractSystemMessage):
    pass


class PoisonPill(AbstractSystemMessage):
    pass


class Continuation(SystemMessage):
    def __init__(self, fun, message):
        self.action = fun
        self.message = message


class SuspendMailbox(SystemMessage):
    pass


class ResumeMailbox(SystemMessage):
    pass


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
