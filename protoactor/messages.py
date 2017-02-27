from abc import ABCMeta

from. import pid, restart_statistics


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
    def __init__(self, who: pid.PID, reason: Exception, crs: restart_statistics.RestartStatistics) -> None:
        self.__who = who
        self.__reason = reason
        self.__crs = crs

    @property
    def who(self) -> pid.PID:
        return self.__who

    @property
    def reason(self) -> Exception:
        return self.__reason

    @property
    def restart_statistics(self) -> restart_statistics.RestartStatistics:
        return self.__crs


class Watch(AbstractSystemMessage):
    def __init__(self, watcher: pid.PID) -> None:
        self.watcher = watcher


class Unwatch(AbstractSystemMessage):
    def __init__(self, watcher: pid.PID) -> None:
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
