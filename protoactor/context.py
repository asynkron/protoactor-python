from abc import ABCMeta, abstractmethod
from datetime import timedelta
from .pid import PID
from .actor import Actor


class Context(metaclass=ABCMeta):
    @property
    @abstractmethod
    def parent(self) -> PID:
        pass

    @property
    @abstractmethod
    def self(self) -> PID:
        pass

    @property
    @abstractmethod
    def sender(self) -> PID:
        pass

    @property
    @abstractmethod
    def message(self) -> PID:
        pass

    @property
    @abstractmethod
    def actor(self) -> Actor:
        pass

    @property
    @abstractmethod
    def receive_timeout(self) -> timedelta:
        pass
