from abc import ABCMeta, abstractmethod
from asyncio import Task
from datetime import timedelta
from typing import Callable

from .restart_statistics import RestartStatistics
from .invoker import AbstractInvoker
from .props import Props
from .pid import PID
from .actor import Actor


class AbstractContext(metaclass=ABCMeta):
    @property
    def parent(self) -> PID:
        return self.__parent

    @parent.setter
    def parent(self, parent: PID):
        self.__parent = parent

    @property
    def my_self(self) -> PID:
        return self.__my_self

    @my_self.setter
    def my_self(self, pid: PID):
        self.__my_self = pid

    @property
    def actor(self) -> Actor:
        return self.__actor

    @actor.setter
    def actor(self, actor: Actor):
        self.__actor = actor

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

    @abstractmethod
    def respond(self, message: object):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def spawn(self, props: Props) -> PID:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def spawn_prefix(self, props: Props, prefix: str) -> PID:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def spawn_named(self, props: Props, name: str) -> PID:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def set_behavior(self, behavior: Callable[[Actor, 'AbstractContext'], [Task]]):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def push_behavior(self, behavior: Callable[[Actor, 'AbstractContext'], [Task]]):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def pop_behavior(self) -> Callable[[Actor, 'AbstractContext'], [Task]]:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def watch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def unwatch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def __incarnate_actor(self):
        raise NotImplementedError("Should Implement this method")


class LocalContext(AbstractContext, AbstractInvoker):
    def __init__(self, producer: Callable[[], Actor], supervisor_strategy, middleware, parent: PID):
        self.__producer = producer
        self.__supervisor_strategy = supervisor_strategy
        self.__middleware = middleware
        self.parent = parent

        self.__stopping: bool = False
        self.__restarting: bool = False
        self.__receive: Callable[[Actor, AbstractContext], [Task]] = None
        self.__restart_statistics: RestartStatistics = None

        self.__behaviour = []
        self.__behaviour.append(self.__actor_receive)
        self.__incarnate_actor()

    def watch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    def pop_behavior(self) -> Callable[[Actor, AbstractContext], [Task]]:
        raise NotImplementedError("Should Implement this method")

    def unwatch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    def spawn(self, props: Props) -> PID:
        raise NotImplementedError("Should Implement this method")

    def set_behavior(self, receive: Callable[[Actor, AbstractContext], [Task]]):
        self.__behaviour.clear()
        self.__behaviour.append(receive)
        self.__receive = receive

    def respond(self, message: object):
        raise NotImplementedError("Should Implement this method")

    def spawn_named(self, props: Props, name: str) -> PID:
        raise NotImplementedError("Should Implement this method")

    def push_behavior(self, behavior: Callable[[Actor, AbstractContext], [Task]]):
        raise NotImplementedError("Should Implement this method")

    def spawn_prefix(self, props: Props, prefix: str) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def stash(self):
        raise NotImplementedError("Should Implement this method")

    @property
    def sender(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def message(self) -> object:
        raise NotImplementedError("Should Implement this method")

    @property
    def receive_timeout(self) -> timedelta:
        raise NotImplementedError("Should Implement this method")

    @property
    def children(self):
        raise NotImplementedError("Should Implement this method")

    # def __actor_receive(self, context: AbstractContext):
    #     return self.actor.receive(context)

    def __incarnate_actor(self):
        self.__restarting = False
        self.__stopping = False
        self.actor = self.__producer()
        self.set_behavior(self.actor.receive)

    # AbstractInvoker Methods
    async def invoke_system_message(self, message: object) -> Task:
        raise NotImplementedError("Should Implement this method")

    async def invoke_user_message(self, message: object) -> Task:
        raise NotImplementedError("Should Implement this method")

    def escalate_failure(self, reason: Exception, message: object):
        if not self.__restart_statistics:
            self.__restart_statistics = RestartStatistics(1, None)

