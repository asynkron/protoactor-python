from abc import ABC, abstractmethod


class RouterManagementMessage(ABC):
    pass


class Routees:
    def __init__(self, pids):
        self.pids = pids


class AddRoutee(RouterManagementMessage):
    def __init__(self, pid):
        self.pid = pid


class RemoveRoutee(RouterManagementMessage):
    def __init__(self, pid):
        self.pid = pid


class BroadcastMessage(RouterManagementMessage):
    def __init__(self, message):
        self.message = message


class GetRoutees(RouterManagementMessage):
    def __init__(self):
        pass


class AbstractHashable(ABC):
    @abstractmethod
    def hash_by(self) -> str:
        raise NotImplementedError('Should implement this method')
