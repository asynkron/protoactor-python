from abc import ABCMeta, abstractmethod, abstractproperty
from asyncio import Task
from datetime import timedelta
from typing import Callable, List, Set

from . import actor, invoker, messages, pid, props, restart_statistics
from .mailbox import messages as mailbox_msg


class AbstractContext(metaclass=ABCMeta):
    @property
    def parent(self) -> pid.PID:
        return self.__parent

    @parent.setter
    def parent(self, parent: pid.PID):
        self.__parent = parent

    @property
    def my_self(self) -> pid.PID:
        return self.__my_self

    @my_self.setter
    def my_self(self, pid: pid.PID):
        self.__my_self = pid

    @property
    def actor(self) -> 'Actor':
        return self.__actor

    @actor.setter
    def actor(self, actor: 'Actor'):
        self.__actor = actor

    @property
    def sender(self) -> pid.PID:
        return self.__sender

    @property
    def message(self) -> object:
        return self.__message

    @message.setter
    def message(self, message: object) -> None:
        self.__message = message

    @property
    def receive_timeout(self) -> timedelta:
        return self.__receive_timeout

    @receive_timeout.setter
    def receive_timeout(self, timeout: timedelta) -> None:
        self.__receive_timeout = timeout

    @property
    @abstractproperty
    def children(self):
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractproperty
    def stash(self):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def respond(self, message: object):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def spawn(self, props: 'Props') -> pid.PID:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def spawn_prefix(self, props: 'Props', prefix: str) -> pid.PID:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def spawn_named(self, props: 'Props', name: str) -> pid.PID:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def set_behavior(self, behavior: Callable[['Actor', 'AbstractContext'], Task]):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def push_behavior(self, behavior: Callable[['Actor', 'AbstractContext'], Task]):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def pop_behavior(self) -> Callable[['Actor', 'AbstractContext'], Task]:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def watch(self, pid: pid.PID):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def unwatch(self, pid: pid.PID):
        raise NotImplementedError("Should Implement this method")


class LocalContext(AbstractContext, invoker.AbstractInvoker):
    def __init__(self, producer: Callable[[], 'Actor'], supervisor_strategy, middleware, parent: pid.PID) -> None:
        self.__producer = producer
        self.__supervisor_strategy = supervisor_strategy
        self.__middleware = middleware
        self.parent = parent

        self.__stopping = False
        self.__restarting = False
        self.__receive = None
        self.__restart_statistics = None

        self.receive_timeout = timedelta(milliseconds=0)

        self.__behaviour = []
        self.__incarnate_actor()

    def watch(self, pid: pid.PID):
        raise NotImplementedError("Should Implement this method")

    def pop_behavior(self) -> Callable[['Actor', AbstractContext], Task]:
        raise NotImplementedError("Should Implement this method")

    def unwatch(self, pid: pid.PID):
        raise NotImplementedError("Should Implement this method")

    def spawn(self, props: 'Props') -> pid.PID:
        raise NotImplementedError("Should Implement this method")

    def set_behavior(self, receive: Callable[['Actor', AbstractContext], Task]):
        self.__behaviour.clear()
        self.__behaviour.append(receive)
        self.__receive = receive

    def respond(self, message: object):
        raise NotImplementedError("Should Implement this method")

    def spawn_named(self, props: 'Props', name: str) -> pid.PID:
        raise NotImplementedError("Should Implement this method")

    def push_behavior(self, behavior: Callable[['Actor', AbstractContext], Task]):
        raise NotImplementedError("Should Implement this method")

    def spawn_prefix(self, props: 'Props', prefix: str) -> pid.PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def stash(self):
        raise NotImplementedError("Should Implement this method")

    @property
    def children(self) -> Set[pid.PID]:
        raise NotImplementedError("Should Implement this method")

    @property
    def watchers(self) -> Set[pid.PID]:
        raise NotImplementedError("Should Implement this method")

    @property
    def watching(self) -> Set[pid.PID]:
        raise NotImplementedError("Should Implement this method")

    # def __actor_receive(self, context: AbstractContext):
    #     return self.actor.receive(context)

    def __incarnate_actor(self):
        self.__restarting = False
        self.__stopping = False
        self.actor = self.__producer()
        self.set_behavior(self.actor.receive)

    # invoker.AbstractInvoker Methods
    async def invoke_system_message(self, message: object) -> None:
        try:
            if isinstance(message, messages.Started):
                await self.invoke_user_message(message)
            elif isinstance(message, messages.Stop):
                await self.__handle_stop()
            elif isinstance(message, messages.Terminated):
                await self.__handle_terminated()
            elif isinstance(message, messages.Watch):
                await self.__handle_watch(message)
            elif isinstance(message, messages.Unwatch):
                await self.__handle_unwatch(message)
            elif isinstance(message, messages.Failure):
                await self.__handle_failure(message)
            elif isinstance(message, messages.Restart):
                await self.handle_restart()
            elif isinstance(message, mailbox_msg.SuspendMailbox):
                pass
            elif isinstance(message, mailbox_msg.ResumeMailbox):
                pass
            else:
                pass

        except Exception as e:
            self.escalate_failure(e, message)

    async def invoke_user_message(self, message: object) -> None:
        influence_timeout = True
        if self.receive_timeout > timedelta(milliseconds=0):
            influence_timeout = not isinstance(message, messages.NotInfluenceReceiveTimeout)
            if influence_timeout is True:
                self._stop_receive_timeout()

        await self._process_message(message)

        if self.receive_timeout > timedelta(milliseconds=0) and influence_timeout is True:
            self._reset_receive_timeout()


    def escalate_failure(self, reason: Exception, message: object) -> None:
        if not self.__restart_statistics:
            self.__restart_statistics = restart_statistics.RestartStatistics(1, None)

    async def __handle_stop(self):
        self.__restarting = False
        self.__stopping = True
        await self.invoke_user_message(messages.Stopping())
        if self.children:
            for child in self.children:
                child.stop()

        await self.__try_restart_or_terminate()

    async def __handle_terminated(self, message: object):
        self.children.remove(message.who)
        self.watching.remove(message.who)
        await self.invoke_user_message(message)
        await self.__try_restart_or_terminate()

    async def __handle_watch(self, message: object):
        if self.watchers is None:
            self.watchers = Set()
        self.watchers.add(message)

    async def __handle_unwatch(self, message: object):
        if self.watchers is not None:
            self.watchers.remove(message)

    async def __handle_failure(self, message: object):
        raise NotImplementedError("Should Implement this method")

    async def handle_restart(self):
        raise NotImplementedError("Should Implement this method")

    def __try_restart_or_terminate(self):
        raise NotImplementedError("Should Implement this method")

    def _stop_receive_timeout(self):
        raise NotImplementedError("Should Implement this method")

    def _reset_receive_timeout(self):
        raise NotImplementedError("Should Implement this method")

    async def _process_message(self, message: object) -> None:
        self.message = message

        if self.__middleware is not None:
            await self.__middleware(self)
        elif isinstance(message, messages.PoisonPill) is True:
            self.my_self.stop()
        else:
            await self.__receive(self)

        self.message = None