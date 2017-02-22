from abc import ABCMeta

from protoactor.pid import PID
from .restart_statistics import RestartStatistics


class AbstractSystemMessage(metaclass=ABCMeta):
    pass


class AutoReceiveMessage(metaclass=ABCMeta):
    pass


class Terminated(AbstractSystemMessage):
    pass


class Restarting:
    pass


class Restart(AbstractSystemMessage):
    pass


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


class Watch(AbstractSystemMessage):
    def __init__(self, watcher: PID) -> None:
        self.watcher = watcher


class Unwatch(AbstractSystemMessage):
    def __init__(self, watcher: PID) -> None:
        self.watcher = watcher


class Stop(AbstractSystemMessage):
    pass


class Stopping(AutoReceiveMessage):
    pass


class Stopped(AutoReceiveMessage):
    pass


class Started(AbstractSystemMessage):
    pass


class ReceiveTimeout(AbstractSystemMessage):
    pass
