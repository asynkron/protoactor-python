from abc import ABCMeta

from. import pid, restart_statistics, utils


class AbstractSystemMessage(metaclass=ABCMeta):
    pass


class AutoReceiveMessage(metaclass=ABCMeta):
    pass


class Terminated(AbstractSystemMessage):
    pass


@utils.singleton
class Restarting:
    pass


@utils.singleton
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

@utils.singleton
class Stop(AbstractSystemMessage):
    pass

@utils.singleton
class Stopping(AutoReceiveMessage):
    pass

@utils.singleton
class Stopped(AutoReceiveMessage):
    pass

@utils.singleton
class Started(AbstractSystemMessage):
    pass

@utils.singleton
class ReceiveTimeout(AbstractSystemMessage):
    pass
