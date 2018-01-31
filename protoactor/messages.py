from abc import ABCMeta
from .restart_statistics import RestartStatistics
from .protos_pb2 import PID
from protoactor.utils import singleton


class AbstractSystemMessage(metaclass=ABCMeta):
    pass


class AutoReceiveMessage(metaclass=ABCMeta):
    pass


class Restarting:
    pass


@singleton
class Stop(AbstractSystemMessage):
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


class Unwatch(AbstractSystemMessage):
    def __init__(self, watcher: PID) -> None:
        self.watcher = watcher


@singleton
class Restarting:
    pass


class Stopping(AutoReceiveMessage):
    pass


class Stopped(AutoReceiveMessage):
    pass


class Started(AbstractSystemMessage):
    pass


class ReceiveTimeout(AbstractSystemMessage):
    pass


class NotInfluenceReceiveTimeout(AbstractSystemMessage):
    pass


class PoisonPill(AbstractSystemMessage):
    pass


class Continuation(SystemMessage):
    def __init__(self, fun, message):
        self.action = fun
        self.message = message
