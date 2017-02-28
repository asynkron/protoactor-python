from abc import ABCMeta, abstractmethod, abstractproperty
from asyncio import Task
from multiprocessing import Process
from typing import Callable


class AbstractDispatcher(metaclass=ABCMeta):
    @property
    @abstractproperty
    def throughput(self) -> int:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def schedule(self, runner: Callable[['AbstractMailbox'], Task]):
        raise NotImplementedError("Should Implement this method")


class ProcessDispatcher(AbstractDispatcher):
    @property
    def throughput(self) -> int:
        raise NotImplementedError("Should Implement this method")

    def schedule(self, runner: Callable[['AbstractMailbox'], Task]):
        p = Process(target=runner)
        p.start()