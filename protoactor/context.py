from abc import ABCMeta, abstractmethod
from datetime import timedelta
from typing import Callable

from .props import Props
from .pid import PID
from .actor import Actor


class AbstractContext(metaclass=ABCMeta):
    @property
    @abstractmethod
    def parent(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def self(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @self.setter
    @abstractmethod
    def self(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def sender(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def message(self) -> object:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def actor(self) -> Actor:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def receive_timeout(self) -> timedelta:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def children(self):
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def stash(self):
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def respond(self, message: object):
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def spawn(self, props:Props) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def spawn_prefix(self, props: Props, prefix: str) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def spawn_named(self, props: Props, name: str) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def set_behavior(self, behavior: Callable[['AbstractContext'], []]):
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def push_behavior(self, behavior: Callable[['AbstractContext'], []]):
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def pop_behavior(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def watch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def unwatch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")


class LocalContext(AbstractContext):
    @property
    def watch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    @property
    def pop_behavior(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def unwatch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    @property
    def spawn(self, props: Props) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def set_behavior(self, behavior: Callable[['AbstractContext'], []]):
        raise NotImplementedError("Should Implement this method")

    @property
    def respond(self, message: object):
        raise NotImplementedError("Should Implement this method")

    @property
    def spawn_named(self, props: Props, name: str) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def push_behavior(self, behavior: Callable[['AbstractContext'], []]):
        raise NotImplementedError("Should Implement this method")

    @property
    def spawn_prefix(self, props: Props, prefix: str) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def stash(self):
        raise NotImplementedError("Should Implement this method")

    def __init__(self, sender: PID, parent: PID, message: object, my_self: PID):
        raise NotImplementedError("Should Implement this method")

    @property
    def sender(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def parent(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def message(self) -> object:
        raise NotImplementedError("Should Implement this method")

    @property
    def self(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def receive_timeout(self) -> timedelta:
        raise NotImplementedError("Should Implement this method")

    @property
    def actor(self) -> Actor:
        raise NotImplementedError("Should Implement this method")

    @property
    def children(self):
        raise NotImplementedError("Should Implement this method")