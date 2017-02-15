from abc import ABCMeta


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
    def __init__(self, who, reason, crs):
        self.__who = who
        self.__reason = reason
        self.__crs = crs

    @property
    def who(self):
        return self.__who

    @property
    def reason(self):
        return self.__reason

    @property
    def restart_statistics(self):
        return self.__crs


class Watch(AbstractSystemMessage):
    pass


class Unwatch(AbstractSystemMessage):
    pass


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
