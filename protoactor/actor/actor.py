import threading
from abc import abstractmethod, ABCMeta
from asyncio import Task
from datetime import timedelta
from enum import Enum

from typing import Callable, List

from protoactor.actor import ProcessRegistry, messages
from protoactor.actor.log import get_logger
from protoactor.actor.message_envelope import MessageEnvelope
from protoactor.actor.process import Guardians, FutureProcess
from protoactor.actor.invoker import AbstractInvoker
from protoactor.actor.message_header import MessageHeader

from protoactor.actor.protos_pb2 import Terminated, Watch, Unwatch, Stop, PID
from protoactor.actor.restart_statistics import RestartStatistics
from protoactor.actor.supervision import AbstractSupervisor, default_strategy
from protoactor.actor.utils import singleton
from protoactor.mailbox.dispatcher import AbstractMessageInvoker
from protoactor.mailbox.messages import ResumeMailbox, SuspendMailbox
from protoactor.actor.messages import Restarting, Started, Stopped, Continuation, ReceiveTimeout, PoisonPill, Failure, \
    Restart

is_import = False
if is_import:
    from protoactor.actor.props import Props


class ContextState(Enum):
    none = 0
    Alive = 1
    Restarting = 2
    Stopping = 3
    Stopped = 4


class AbstractSenderContext(metaclass=ABCMeta):
    def __init__(self):
        self.__headers = None

    @property
    def headers(self) -> MessageHeader:
        return self.__headers

    @property
    @abstractmethod
    def message(self) -> any:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def send(self, target: PID, message: any):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def request(self, target: PID, message: any):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def request_async(self, target: PID, message: any):
        raise NotImplementedError("Should Implement this method")


class AbstractReceiverContext(metaclass=ABCMeta):
    @abstractmethod
    async def receive(self, envelope: MessageEnvelope):
        raise NotImplementedError("Should Implement this method")


class AbstractSpawnContext(metaclass=ABCMeta):
    @abstractmethod
    def spawn(self, props: 'Props') -> PID:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def spawn_prefix(self, props: 'Props', prefix: str) -> PID:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def spawn_named(self, props: 'Props', name: str) -> PID:
        raise NotImplementedError("Should Implement this method")


class AbstractRootContext(AbstractSpawnContext, AbstractSenderContext, metaclass=ABCMeta):
    pass


class AbstractContext(AbstractSenderContext, AbstractReceiverContext, AbstractSpawnContext):
    def __init__(self):
        super().__init__()
        self._receive_timeout = None
        self._actor = None
        self._my_self = None
        self._parent = None

    @property
    def parent(self) -> PID:
        return self._parent

    @property
    def my_self(self) -> PID:
        return self._my_self

    @my_self.setter
    def my_self(self, value) -> PID:
        self._my_self = value

    @property
    @abstractmethod
    def sender(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    def actor(self) -> 'Actor':
        return self._actor

    @property
    def receive_timeout(self) -> timedelta:
        return self._receive_timeout

    @property
    @abstractmethod
    def children(self):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def respond(self, message: object):
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def stash(self):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def watch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def unwatch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def set_receive_timeout(self, receive_timeout: timedelta) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def cancel_receive_timeout(self) -> None:
        raise NotImplementedError("Should Implement this method")

    # @abstractmethod
    # def _incarnate_actor(self):
    #     raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def tell(self, target: PID, message: object):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def reenter_after(self, target: Task, action: Callable):
        raise NotImplementedError("Should Implement this method")


class RootContext(AbstractRootContext):
    def __init__(self, headers=None, sender_middleware=None):
        super().__init__()
        self.__headers = headers
        self.__sender_middleware = sender_middleware
        self._message = None

    @property
    def headers(self):
        return self.__headers

    @property
    def sender_middleware(self):
        return self.__sender_middleware

    @property
    def message(self):
        return self._message

    def spawn(self, props):
        name = ProcessRegistry().next_id()
        return self.spawn_named(props, name)

    def spawn_named(self, props, name):
        if props.guardian_strategy is not None:
            parent = Guardians().get_guardian_pid(props.guardian_strategy)
        else:
            parent = None
        return props.spawn(name, parent)

    def spawn_prefix(self, props, prefix):
        name = prefix + ProcessRegistry().next_id()
        return self.spawn_named(props, name)

    def with_headers(self, headers):
        return self.__copy_with({'_Props__headers': headers})

    def with_sender_middleware(self, middleware):
        return self.__copy_with({'_Props__sender_middleware': middleware})

    def default_sender(self, context, target, message):
        target.send_user_message(message)

    def send(self, target, message):
        self.send_user_message(target, message)

    def request(self, target, message, sender=None):
        if sender is None:
            self.send_user_message(target, message)
        else:
            self.send(target, MessageEnvelope(message, sender, None))

    async def request_async(self, target, message, cancellation_token=None, timeout=None):
        if cancellation_token is not None and timeout is None:
            future = FutureProcess(cancellation_token)
            message_envelope = MessageEnvelope(message, future.pid, None)
            self.send_user_message(target, message_envelope)
            return await future.task
        elif cancellation_token is None and timeout is not None:
            future = FutureProcess()
            message_envelope = MessageEnvelope(message, future.pid, None)
            self.send_user_message(target, message_envelope)
            await future.cancellable_wait(timeout)
            return await future.task
        else:
            future = FutureProcess()
            message_envelope = MessageEnvelope(message, future.pid, None)
            self.send_user_message(target, message_envelope)
            return await future.task

    def send_user_message(self, target, message):
        if self.__sender_middleware is not None:
            if isinstance(message, MessageEnvelope):
                self.__sender_middleware(self, target, message)
            else:
                self.__sender_middleware(self, target, MessageEnvelope(message, None, None))
        else:
            target.send_user_message(message)

    def __copy_with(self, new_params):
        params = self.__dict__
        params.update(new_params)

        _params = {}
        for key in params:
            new_key = key.replace('_Props__', '')
            _params[new_key] = params[key]

        return RootContext(**_params)


class ActorContext(AbstractContext, AbstractInvoker, AbstractSupervisor, AbstractMessageInvoker):

    def __init__(self, producer: Callable[[], 'Actor'], supervisor_strategy, middleware, parent: PID) -> None:
        super().__init__()
        self.__producer = producer
        self.__supervisor_strategy = supervisor_strategy
        self.__middleware = middleware
        self._parent = parent

        self.__stopping = False
        self.__restarting = False
        self.__receive = None
        self.__restart_statistics = None

        self._receive_timeout = timedelta(milliseconds=0)
        self.__behaviour = []

        self.__timer = None
        self.__stash = []
        self.__state = ContextState.none
        self.__children = []
        self.__watchers = []
        self.__message_or_envelope = None

        self._incarnate_actor()
        self.__logger = get_logger('ActorContext')

    @property
    def message(self) -> any:
        return MessageEnvelope.unwrap_message(self.__message_or_envelope)

    @property
    def sender(self) -> PID:
        return MessageEnvelope.unwrap_sender(self.__message_or_envelope)

    @property
    def children(self) -> List[PID]:
        return self.__children

    def watch(self, pid: PID):
        pid.send_system_message(Watch(watcher=self.my_self))

    def unwatch(self, pid: PID):
        pid.send_system_message(Unwatch(watcher=self.my_self))

    def spawn(self, props: 'Props') -> PID:
        p_id = ProcessRegistry().next_id()
        return self.spawn_named(props, p_id)

    def set_behavior(self, receive: Callable[['Actor', AbstractContext], Task]):
        self.__behaviour.clear()
        self.__behaviour.append(receive)
        self.__receive = receive

    def respond(self, message: object):
        self.send(self.sender, message)

    def spawn_named(self, props: 'Props', name: str) -> PID:
        # TODO: check for guardian

        pid = props.spawn('{0}/{1}'.format(self.my_self, name), self.my_self)
        self.__children.append(pid)
        return pid

    def spawn_prefix(self, props: 'Props', prefix: str) -> PID:
        p_id = prefix + ProcessRegistry().next_id()
        return self.spawn_named(props, p_id)

    def stash(self):
        self.__stash.append(self.message)

    async def receive(self, envelope: object, timeout: timedelta = None):
        if timeout is None:
            self.__message_or_envelope = envelope
            return self.__middleware(self) if self.__middleware is not None else self.__default_receive(self)

    async def request_async(self, target: PID, message: object):
        future = FutureProcess()
        message_envelope = MessageEnvelope(message, future.pid, None)
        self.__send_user_message(target, message_envelope)
        return future.task

    def send(self, target: PID, message: any):
        self.__send_user_message(target, message)

    def tell(self, target: PID, message: any):
        self.__send_user_message(target, message)

    def request(self, message: any, target: PID):
        message_envelope = MessageEnvelope(message, self.my_self, None)
        self.__send_user_message(target, message_envelope)

    def set_receive_timeout(self, receive_timeout: timedelta) -> None:
        if receive_timeout == self.receive_timeout:
            return None

        self.__stop_receive_timeout()
        self._receive_timeout = receive_timeout

        if self.__timer is None:
            self.__timer = threading.Timer(self.__get_receive_timeout_seconds(), self._receive_timeout_callback)
        else:
            self.reset_receive_timeout()

    def _incarnate_actor(self):
        self.__state = ContextState.Alive
        self._actor = self.__producer()
        self.set_behavior(self.actor.receive)

    def __get_receive_timeout_seconds(self):
        return self.receive_timeout.total_seconds()

    def resume_children(self, *pids: List['PID']) -> None:
        for pid in pids:
            pid.send_system_message(ResumeMailbox())

    def stop_children(self, *pids: List['PID']) -> None:
        for pid in pids:
            pid.send_system_message(Stop())

    def restart_children(self, reason: Exception, *pids: List['PID']) -> None:
        for pid in pids:
            pid.send_system_message(Restart(reason))

    async def invoke_system_message(self, message: any) -> None:
        try:
            if isinstance(message, messages.Started):
                return await self.invoke_user_message(message)
            elif isinstance(message, Stop):
                await self.__handle_stop()
            elif isinstance(message, Terminated):
                await self.__handle_terminated(message)
            elif isinstance(message, Watch):
                await self.__handle_watch(message)
            elif isinstance(message, Unwatch):
                return await self.__handle_unwatch(message)
            elif isinstance(message, messages.Failure):
                return await self.__handle_failure(message)
            elif isinstance(message, messages.Restart):
                return await self.handle_restart()
            elif isinstance(message, SuspendMailbox):
                return None
            elif isinstance(message, ResumeMailbox):
                return None
            else:
                self.__logger.warn("Unknown system message {0}".format(message))
                return None

        except Exception as e:
            # self.__logger.error("Error handling SystemMessage {0}".format(str(e)))
            # TODO: .Net implementation is just throwing exception upper.
            self.escalate_failure(e, message)

    def __send_user_message(self, target, message):
        # TODO: check for middleware

        target.send_user_message(message)

    async def invoke_user_message(self, message: any) -> None:
        influence_timeout = True
        if self.receive_timeout > timedelta(milliseconds=0):
            influence_timeout = not isinstance(message, messages.NotInfluenceReceiveTimeout)
            if influence_timeout is True:
                self.__stop_receive_timeout()

        await self._process_message(message)

        if self.receive_timeout > timedelta(milliseconds=0) and influence_timeout is True:
            self.reset_receive_timeout()

    def escalate_failure(self, reason: Exception, obj: object) -> None:
        if self.__restart_statistics is None:
            self.__restart_statistics = RestartStatistics(0, None)

        failure = Failure(self.my_self, reason, self.__restart_statistics)
        self.my_self.send_system_message(SuspendMailbox())

        if self.parent is None:
            self.__handle_root_failure(failure)
        else:
            self.parent.send_system_message(failure)

    async def __handle_stop(self):
        if self.__state == ContextState.Stopping:
            return

        self.__state = ContextState.Stopping
        self.cancel_receive_timeout()

        await self.invoke_user_message(messages.Stopping())
        await self.__stop_all_children()

    async def __stop_all_children(self):
        for child in self.children:
            child.stop()
        await self.__try_restart_or_stop()

    async def __handle_terminated(self, message: Terminated):
        if message.who in self.children:
            self.children.remove(message.who)
        await self.invoke_user_message(message)
        await self.__try_restart_or_stop()

    async def __handle_watch(self, message: Watch):
        if self.__state == ContextState.Stopping:
            message.watcher.send_system_message(Terminated(who=self.my_self, address_terminated=False))
        else:
            self.__watchers.append(message.watcher)

    async def __handle_unwatch(self, message: Unwatch):
        if self.__watchers is not None:
            self.__watchers.remove(message.watcher)

    async def __handle_failure(self, message: object):
        # TODO: check if actor implements ISupervisorStrategy
        self.__supervisor_strategy.handle_failure(self, message.who, message.restart_statistics, message.reason)

    async def handle_restart(self):
        self.__state = ContextState.Restarting
        await self.invoke_user_message(Restarting())

        process_registry = ProcessRegistry()
        if self.children is not None:
            for child in self.children:
                process_registry.get(child).stop(child)

        await self.__try_restart_or_stop()

    async def __try_restart_or_stop(self):
        if len(self.children) > 0:
            return

        if self.__state == ContextState.Restarting:
            await self.__restart()
        elif self.__state == ContextState.Stopping:
            await self.__finalize_stop()

    async def __restart(self):
        self.__dispose_actor_if_disposable()
        self._incarnate_actor()
        self.my_self.send_system_message(ResumeMailbox())

        await self.invoke_user_message(Started())

        if self.__stash is not None:
            while len(self.__stash) > 0:
                msg = self.__stash.pop()
                await self.invoke_user_message(msg)

    async def __finalize_stop(self):
        ProcessRegistry().remove(self.my_self)
        await self.invoke_user_message(Stopped())

        self.__dispose_actor_if_disposable()

        if self.__watchers is not None:
            for watcher in self.__watchers:
                watcher.send_system_message(Terminated(who=self.my_self))
        elif self.parent is not None:
            self.parent.send_system_message(Terminated(who=self.my_self))

        self.__state = ContextState.Stopped

    def __stop_receive_timeout(self):
        self.__timer.cancel()

    def reset_receive_timeout(self):
        self.__timer.cancel()
        self.__timer = threading.Timer(self.__timer.interval, self.__timer.function)
        self.__timer.start()

    def cancel_receive_timeout(self):
        if self.__timer is None:
            return

        self.__stop_receive_timeout()
        self.__timer = None
        self._receive_timeout = None

    def reenter_after(self, target: Task, action: Callable):
        msg = self._message

        def act():
            action()
            return None

        cont = Continuation(act, msg)

        target.add_done_callback(lambda _: self.my_self.send_system_message(cont))

    def _receive_timeout_callback(self):
        if self.__timer is None:
            return

        self.cancel_receive_timeout()

        pr = ProcessRegistry()
        reff = pr.get(self.my_self)
        message_env = MessageEnvelope(ReceiveTimeout(), None, None)
        reff.send_user_message(self.my_self, message_env)

    async def _process_message(self, message: object) -> None:
        # TODO: port this method from .Net implementation.
        self.__message_or_envelope = message

        if self.__middleware is not None:
            await self.__middleware(self)
        elif isinstance(message, messages.PoisonPill) is True:
            self.my_self.stop()
        else:
            await self.__receive(self)

        self.__message_or_envelope = None

    def __handle_root_failure(self, failure):
        default_strategy.handle_failure(self, failure.who, failure.restart_statistics, failure.reason)

    def __dispose_actor_if_disposable(self):
        atr = getattr(self._actor, "__exit__", None)
        if callable(atr):
            self._actor.__exit__()

    def __default_receive(self, context):
        # pr = ProcessRegistry()
        if context.message is PoisonPill:
            context.my_self.stop()
            # pr.get(context.my_self).stop(context.my_self)
            return None

        return context.actor.receive(context)


class Actor():
    @abstractmethod
    async def receive(self, context: AbstractContext) -> None:
        pass


class EmptyActor(Actor):
    def __init__(self, receive):
        self._receive = receive

    async def receive(self, context):
        await self._receive(context)


class GlobalRootContext(metaclass=singleton):

    def __init__(self):
        self.__instance = RootContext()

    @property
    def instance(self):
        return self.__instance
