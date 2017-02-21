from abc import ABCMeta, abstractmethod
from asyncio import Task
from typing import Callable
from multiprocessing import Process

from .mailbox.mailbox import AbstractMailbox


class AbstractDispatcher(metaclass=ABCMeta):
    @property
    @abstractmethod
    def throughput(self) -> int:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def schedule(self, runner: Callable[[AbstractMailbox], Task]):
        raise NotImplementedError("Should Implement this method")


class ProcessDispatcher(AbstractDispatcher):
    @property
    def throughput(self) -> int:
        raise NotImplementedError("Should Implement this method")

    def schedule(self, runner: Callable[[AbstractMailbox], Task]):
        p = Process(target=runner)
        p.start()