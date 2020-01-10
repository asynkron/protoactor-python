import asyncio
from abc import abstractmethod, ABCMeta
from asyncio import Task, Future
from datetime import timedelta
from enum import Enum
from functools import reduce
from inspect import signature
from typing import Callable, List, Awaitable, Any

from protoactor.actor import messages
from protoactor.actor.cancel_token import CancelToken
from protoactor.actor.log import get_logger
from protoactor.actor.message_envelope import MessageEnvelope
from protoactor.actor.message_header import MessageHeader
from protoactor.actor.messages import Restarting, Started, Stopped, \
    Continuation, ReceiveTimeout, PoisonPill, Failure, Restart, \
    SystemMessage, NotInfluenceReceiveTimeout, ResumeMailbox, \
    SuspendMailbox
from protoactor.actor.process import Guardians, FutureProcess, ProcessRegistry
from protoactor.actor.protos_pb2 import Terminated, Watch, Unwatch, Stop, PID
from protoactor.actor.restart_statistics import RestartStatistics
from protoactor.actor.supervision import AbstractSupervisor, Supervision, \
    AbstractSupervisorStrategy
from protoactor.mailbox.dispatcher import AbstractMessageInvoker
from protoactor.utils.async_timer import AsyncTimer

is_import = False
if is_import:
    from protoactor.actor.props import Props
    from protoactor.actor.actor import Actor


class ContextState(Enum):
    none = 0
    Alive = 1
    Restarting = 2
    Stopping = 3
    Stopped = 4


class AbstractSenderContext(metaclass=ABCMeta):
    @property
    @abstractmethod
    def headers(self) -> MessageHeader:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def message(self) -> any:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def send(self, target: PID, message: any):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def request(self, target: PID, message: any, sender: PID = None):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def request_future(self, target: PID,
                             message: object,
                             timeout: timedelta = None,
                             cancellation_token: CancelToken = None) -> asyncio.Future:
        raise NotImplementedError("Should Implement this method")


class AbstractReceiverContext(metaclass=ABCMeta):
    @abstractmethod
    async def receive(self, envelope: MessageEnvelope):
        raise NotImplementedError("Should Implement this method")


class AbstractSpawnerContext(metaclass=ABCMeta):
    @abstractmethod
    def spawn(self, props: 'Props') -> PID:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def spawn_prefix(self, props: 'Props', prefix: str) -> PID:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def spawn_named(self, props: 'Props', name: str) -> PID:
        raise NotImplementedError("Should Implement this method")


class AbstractStopperContext(metaclass=ABCMeta):
    @abstractmethod
    async def stop(self, pid: PID) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def stop_future(self, pid: PID) -> Future:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def poison(self, pid: PID) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def poison_future(self, pid: PID) -> Future:
        raise NotImplementedError("Should Implement this method")


class AbstractRootContext(AbstractSpawnerContext, AbstractSenderContext, AbstractStopperContext, metaclass=ABCMeta):
    pass


class AbstractContext(AbstractSenderContext, AbstractReceiverContext, AbstractSpawnerContext, AbstractStopperContext):
    @property
    @abstractmethod
    def parent(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def my_self(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @my_self.setter
    @abstractmethod
    def my_self(self, value) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def sender(self) -> PID:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def actor(self) -> 'Actor':
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def receive_timeout(self) -> timedelta:
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def children(self):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def respond(self, message: object):
        raise NotImplementedError("Should Implement this method")

    @property
    @abstractmethod
    def stash(self):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def watch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def unwatch(self, pid: PID):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def set_receive_timeout(self, receive_timeout: timedelta) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def cancel_receive_timeout(self) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def forward(self, target: PID) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def reenter_after(self, target: Task, action: Callable):
        raise NotImplementedError("Should Implement this method")


class RootContext(AbstractRootContext):
    def __init__(self, message_header=MessageHeader(), middleware=None):
        super().__init__()
        self._message = None
        self._headers = message_header
        if middleware is None:
            self._sender_middleware = None
        else:
            self._sender_middleware = reduce(lambda inner, outer: outer(inner), list(reversed(middleware)),
                                             self.default_sender)

    @property
    def headers(self):
        return self._headers

    @property
    def sender_middleware(self):
        return self._sender_middleware

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

    async def default_sender(self, context, target, message):
        await target.send_user_message(message)

    async def send(self, target, message):
        await self.send_user_message(target, message)

    async def request(self, target, message, sender=None):
        if sender is None:
            await self.send_user_message(target, message)
        else:
            await self.send(target, MessageEnvelope(message, sender, None))

    async def request_future(self, target: PID, message: object, timeout: timedelta = None,
                             cancellation_token: CancelToken = None) -> asyncio.Future:
        if timeout is None and cancellation_token is None:
            future = FutureProcess()
            message_envelope = MessageEnvelope(message, future.pid, None)
            await self.send_user_message(target, message_envelope)
            return await future.task
        elif timeout is not None and cancellation_token is None:
            future = FutureProcess()
            message_envelope = MessageEnvelope(message, future.pid, None)
            await self.send_user_message(target, message_envelope)
            return await CancelToken('token', asyncio.get_event_loop()).cancellable_wait(future.task,
                                                                                         timeout=timeout.total_seconds())
        elif timeout is None and cancellation_token is not None:
            future = FutureProcess(cancellation_token)
            message_envelope = MessageEnvelope(message, future.pid, None)
            await self.send_user_message(target, message_envelope)
            return await future.task
        else:
            future = FutureProcess(cancellation_token)
            message_envelope = MessageEnvelope(message, future.pid, None)
            await self.send_user_message(target, message_envelope)
            return await cancellation_token.cancellable_wait(future.task, timeout=timeout.total_seconds())

    async def send_user_message(self, target, message):
        if self._sender_middleware is not None:
            await self._sender_middleware(self, target, MessageEnvelope.wrap(message))
        else:
            await target.send_user_message(message)

    async def stop(self, pid: PID) -> None:
        reff = ProcessRegistry().get(pid)
        await reff.stop(pid)

    async def stop_future(self, pid: PID) -> Future:
        future = FutureProcess()
        await pid.send_system_message(Watch(watcher=future.pid))
        await self.stop(pid)
        return future.task

    async def poison(self, pid: PID) -> None:
        await pid.send_system_message(PoisonPill())

    async def poison_future(self, pid: PID) -> Future:
        future = FutureProcess()
        await pid.send_system_message(Watch(watcher=future.pid))
        await self.poison(pid)
        return future.task

    def __copy_with(self, new_params):
        params = self.__dict__
        params.update(new_params)

        _params = {}
        for key in params:
            new_key = key.replace('_Props__', '')
            _params[new_key] = params[key]

        return RootContext(**_params)


class ActorContextExtras():
    def __init__(self, context: AbstractContext):
        self._children = []
        self._receive_timeout_timer = None
        self._stash = []
        self._watchers = []
        self._context = context

    @property
    def children(self) -> List[PID]:
        return self._children

    @property
    def receive_timeout_timer(self) -> AsyncTimer:
        return self._receive_timeout_timer

    @property
    def restart_statistics(self) -> RestartStatistics:
        return RestartStatistics(0, None)

    @property
    def stash(self) -> List[object]:
        return self._stash

    @property
    def watchers(self) -> List[PID]:
        return self._watchers

    @property
    def context(self) -> AbstractContext:
        return self._context

    def init_receive_timeout_timer(self, timer: AsyncTimer) -> None:
        self._receive_timeout_timer = timer

    def reset_receive_timeout_timer(self) -> None:
        self._receive_timeout_timer.cancel()
        self._receive_timeout_timer = AsyncTimer(self._receive_timeout_timer.interval,
                                                 self._receive_timeout_timer.function)
        self._receive_timeout_timer.start()

    def stop_receive_timeout_timer(self) -> None:
        self._receive_timeout_timer.cancel()

    def kill_receive_timeout_timer(self) -> None:
        self._receive_timeout_timer.cancel()
        self._receive_timeout_timer = None

    def add_child(self, pid: PID) -> None:
        if pid not in self._children:
            self._children.append(pid)

    def remove_child(self, pid: PID) -> None:
        if pid in self._children:
            self._children.remove(pid)

    def watch(self, pid: PID) -> None:
        if pid not in self._watchers:
            self._watchers.append(pid)

    def unwatch(self, pid: PID) -> None:
        if pid in self._watchers:
            self._watchers.remove(pid)


class AbstractActorContext(AbstractContext, AbstractSupervisor, AbstractMessageInvoker, metaclass=ABCMeta):
    pass


class ActorContext(AbstractActorContext):
    def __init__(self, props: 'Props', parent: PID) -> None:
        self._actor = None
        self._my_self = None
        self._props = props
        self._parent = parent
        self._empty_children = []
        self._extras = None
        self._message_or_envelope = None
        self._state = None
        self._logger = get_logger('ActorContext')
        self._receive_timeout = timedelta()

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
    def children(self) -> List[PID]:
        if self._extras is not None:
            return self._extras.children
        else:
            return self._empty_children

    @property
    def actor(self) -> 'Actor':
        return self._actor

    @property
    def receive_timeout(self) -> timedelta:
        return self._receive_timeout

    @property
    def message(self) -> any:
        return MessageEnvelope.unwrap_message(self._message_or_envelope)

    @property
    def sender(self) -> PID:
        return MessageEnvelope.unwrap_sender(self._message_or_envelope)

    @property
    def headers(self) -> PID:
        return MessageEnvelope.unwrap_header(self._message_or_envelope)

    def stash(self) -> None:
        self._ensure_extras().stash.append(self.message)

    async def respond(self, message: object) -> None:
        await self.send(self.sender, message)

    def spawn(self, props: 'Props') -> PID:
        p_id = ProcessRegistry().next_id()
        return self.spawn_named(props, p_id)

    def spawn_prefix(self, props: 'Props', prefix: str) -> PID:
        p_id = prefix + ProcessRegistry().next_id()
        return self.spawn_named(props, p_id)

    def spawn_named(self, props: 'Props', name: str) -> PID:
        if props.guardian_strategy is not None:
            raise ValueError('Props used to spawn child cannot have GuardianStrategy.')

        pid = props.spawn(f'{self.my_self}/{name}', self.my_self)

        self._ensure_extras().add_child(pid)
        return pid

    async def watch(self, pid: PID) -> None:
        await pid.send_system_message(Watch(watcher=self.my_self))

    async def unwatch(self, pid: PID) -> None:
        await pid.send_system_message(Unwatch(watcher=self.my_self))

    def set_receive_timeout(self, duration: timedelta) -> None:
        if duration.total_seconds() <= 0:
            raise ValueError('Duration must be greater than zero')
        if duration == self.receive_timeout:
            return None

        self.__stop_receive_timeout()
        self._receive_timeout = duration

        self._ensure_extras()
        if self._extras.receive_timeout_timer is None:
            self._extras.init_receive_timeout_timer(AsyncTimer(self._receive_timeout,
                                                               self.__receive_timeout_callback))
        else:
            self.__reset_receive_timeout()

    def cancel_receive_timeout(self):
        if self._extras.receive_timeout_timer is None:
            return

        self.__stop_receive_timeout()
        self._extras.kill_receive_timeout_timer()

        self._receive_timeout = timedelta()

    async def send(self, target: PID, message: any) -> None:
        await self.__send_user_message(target, message)

    async def forward(self, target: PID) -> None:
        if isinstance(self._message_or_envelope, SystemMessage):
            self._logger.log_warning(f'SystemMessage cannot be forwarded. {self._message_or_envelope}')
            
            return
        await self.__send_user_message(target, self._message_or_envelope)

    async def request(self, target: PID, message: any) -> None:
        message_envelope = MessageEnvelope(message, self.my_self, None)
        await self.__send_user_message(target, message_envelope)

    def reenter_after(self, target: Callable[[], Awaitable[Any]], action: Callable[[Any], None]) -> None:
        async def run(msg):
            if isinstance(target, Future):
                # await target
                await asyncio.wait([target])
                result = target
            else:
                loop = asyncio.get_event_loop()
                future = loop.create_future()
                try:
                    future.set_result(await target())
                except Exception as ex:
                    future.set_exception(ex)
                result = future
            if len(list(signature(action).parameters)) == 0:
                async def fn():
                    return await action()

                await self.my_self.send_system_message(Continuation(fn, msg))
            else:
                async def fn():
                    return await action(result)

                await self.my_self.send_system_message(Continuation(fn, msg))

        asyncio.ensure_future(run(self._message_or_envelope))

    async def request_future(self, target: PID, message: object, timeout: timedelta = None,
                             cancellation_token: CancelToken = None) -> asyncio.Future:
        if timeout is None and cancellation_token is None:
            future = FutureProcess()
            message_envelope = MessageEnvelope(message, future.pid, None)
            await self.__send_user_message(target, message_envelope)
            return await future.task
        elif timeout is not None and cancellation_token is None:
            future = FutureProcess()
            message_envelope = MessageEnvelope(message, future.pid, None)
            await self.__send_user_message(target, message_envelope)
            return await CancelToken('token', asyncio.get_event_loop()).cancellable_wait(future.task,
                                                                                         timeout=timeout.total_seconds()
                                                                                         )
        elif timeout is None and cancellation_token is not None:
            future = FutureProcess(cancellation_token)
            message_envelope = MessageEnvelope(message, future.pid, None)
            await self.__send_user_message(target, message_envelope)
            return await future.task
        else:
            future = FutureProcess(cancellation_token)
            message_envelope = MessageEnvelope(message, future.pid, None)
            await self.__send_user_message(target, message_envelope)
            return await cancellation_token.cancellable_wait(future.task, timeout=timeout.total_seconds())

    async def escalate_failure(self, reason: Exception, who: 'PID'):
        failure = Failure(self.my_self, reason, self._ensure_extras().restart_statistics)
        await self.my_self.send_system_message(SuspendMailbox())
        if self.parent is None:
            await self.__handle_root_failure(failure)
        else:
            await self.parent.send_system_message(failure)

    async def restart_children(self, reason: Exception, *pids: List['PID']) -> None:
        for pid in pids:
            await pid.send_system_message(Restart(reason))

    async def stop_children(self, *pids: List['PID']) -> None:
        for pid in pids:
            await pid.send_system_message(Stop())

    async def resume_children(self, *pids: List['PID']) -> None:
        for pid in pids:
            await pid.send_system_message(ResumeMailbox())

    async def invoke_system_message(self, message: any) -> None:
        try:
            if isinstance(message, messages.Started):
                self.__incarnate_actor()
                return await self.invoke_user_message(message)
            elif isinstance(message, Stop):
                await self.__initiate_stop()
            elif isinstance(message, Terminated):
                await self.__handle_terminated(message)
            elif isinstance(message, Watch):
                await self.__handle_watch(message)
            elif isinstance(message, Unwatch):
                return await self.__handle_unwatch(message)
            elif isinstance(message, messages.Failure):
                return await self.__handle_failure(message)
            elif isinstance(message, messages.Restart):
                return await self.__handle_restart()
            elif isinstance(message, SuspendMailbox):
                return None
            elif isinstance(message, ResumeMailbox):
                return None
            elif isinstance(message, Continuation):
                self._message_or_envelope = message.message
                return await message.action()
            else:
                self._logger.warn(f'Unknown system message {message}')
                return None
        except Exception as e:
            self._logger.error(f'Error handling SystemMessage {str(e)}')
            raise Exception()

    async def invoke_user_message(self, message: any) -> None:
        if self._state == ContextState.Stopped:
            self._logger.error(f'Actor already stopped, ignore user message {str(message)}')
            return

        influence_timeout = True
        if self.receive_timeout > timedelta():
            not_influence_timeout = isinstance(message, NotInfluenceReceiveTimeout)
            influence_timeout = not not_influence_timeout
            if influence_timeout is True:
                self.__stop_receive_timeout()

        await self.__process_message(message)

        if self.receive_timeout > timedelta() and influence_timeout:
            self.__reset_receive_timeout()

    async def receive(self, envelope: MessageEnvelope):
        self._message_or_envelope = envelope
        return await self.__default_receive()

    async def stop(self, pid: PID) -> None:
        reff = ProcessRegistry().get(pid)
        await reff.stop(pid)

    async def stop_future(self, pid: PID) -> Future:
        future = FutureProcess()
        await pid.send_system_message(Watch(watcher=future.pid))
        await self.stop(pid)
        return future.task

    async def poison(self, pid: PID) -> None:
        await pid.send_system_message(PoisonPill())

    async def poison_future(self, pid: PID) -> Future:
        future = FutureProcess()
        await pid.send_system_message(Watch(watcher=future.pid))
        await self.poison(pid)
        return future.task

    async def __default_receive(self):
        if isinstance(self.message, PoisonPill):
            await self.my_self.stop()
            return

        if self._props.context_decorator_chain is not None:
            return await self.actor.receive(self._ensure_extras().context)

        return await self.actor.receive(self)

    async def __process_message(self, message: object) -> asyncio.futures:
        if self._props.receive_middleware_chain is not None:
            return await self._props.receive_middleware_chain(self._ensure_extras().context,
                                                              MessageEnvelope.wrap(message))
        if self._props.context_decorator_chain is not None:
            return await self._ensure_extras().context.receive(MessageEnvelope.wrap(message))

        self._message_or_envelope = message
        return await self.__default_receive()

    async def __send_user_message(self, target, message):
        if self._props.sender_middleware_chain is not None:
            await self._props.sender_middleware_chain(self._ensure_extras().context,
                                                      target,
                                                      MessageEnvelope.wrap(message))
        else:
            await target.send_user_message(message)

    def __incarnate_actor(self):
        self._state = ContextState.Alive
        self._actor = self._props.producer()

    async def __handle_restart(self):
        self._state = ContextState.Restarting
        self.cancel_receive_timeout()
        await self.invoke_user_message(Restarting())
        await self.__stop_all_children()

    async def __handle_unwatch(self, message: Unwatch):
        if self._extras is not None:
            self._extras.unwatch(message.watcher)

    async def __handle_watch(self, message: Watch):
        if self._state == ContextState.Stopping:
            await message.watcher.send_system_message(Terminated(who=self.my_self, address_terminated=False))
        else:
            self._ensure_extras().watch(message.watcher)

    async def __handle_failure(self, message: Failure):
        if isinstance(self.actor, AbstractSupervisorStrategy):
            await self.actor.handle_failure(self, message.who, message.restart_statistics, message.reason)
        else:
            await self._props.supervisor_strategy.handle_failure(self,
                                                                 message.who,
                                                                 message.restart_statistics,
                                                                 message.reason)

    async def __handle_terminated(self, message: Terminated):
        if self._extras is not None:
            self._extras.remove_child(message.who)
        await self.invoke_user_message(message)
        if self._state == ContextState.Stopping or self._state == ContextState.Restarting:
            await self.__try_restart_or_stop()

    async def __handle_root_failure(self, failure):
        await Supervision.default_strategy.handle_failure(self, failure.who, failure.restart_statistics, failure.reason)

    async def __initiate_stop(self):
        if self._state == ContextState.Stopping:
            return

        self._state = ContextState.Stopping
        self.cancel_receive_timeout()
        await self.invoke_user_message(messages.Stopping())
        await self.__stop_all_children()

    async def __stop_all_children(self):
        if self._extras is not None:
            if self._extras.children is not None:
                for child in self._extras.children:
                    await child.stop()
        await self.__try_restart_or_stop()

    async def __try_restart_or_stop(self):
        if self._extras is not None:
            if self._extras.children is not None:
                if len(self._extras.children) > 0:
                    return

        if self._state == ContextState.Restarting:
            await self.__restart()
        elif self._state == ContextState.Stopping:
            await self.__finalize_stop()

    async def __finalize_stop(self):
        ProcessRegistry().remove(self.my_self)
        await self.invoke_user_message(Stopped())

        self.__dispose_actor_if_disposable()

        if self._extras is not None:
            for watcher in self._extras.watchers:
                await watcher.send_system_message(Terminated(who=self.my_self))

        if self._parent is not None:
            await self._parent.send_system_message(Terminated(who=self.my_self))

        self._state = ContextState.Stopped

    async def __restart(self):
        self.__dispose_actor_if_disposable()
        self.__incarnate_actor()
        self.my_self.send_system_message(ResumeMailbox())

        await self.invoke_user_message(Started())

        if self._extras.stash is not None:
            while len(self._extras.stash) > 0:
                msg = self._extras.stash.pop()
                await self.invoke_user_message(msg)

    def __dispose_actor_if_disposable(self):
        atr = getattr(self._actor, "__exit__", None)
        if callable(atr):
            self._actor.__exit__()

    def __reset_receive_timeout(self):
        if self._extras is not None:
            if self._extras.receive_timeout_timer is not None:
                self._extras.reset_receive_timeout_timer()

    def __stop_receive_timeout(self):
        if self._extras is not None:
            if self._extras.receive_timeout_timer is not None:
                self._extras.stop_receive_timeout_timer()

    async def __receive_timeout_callback(self):
        if self._extras is None or self._extras.receive_timeout_timer is None:
            return

        self.cancel_receive_timeout()
        await self.send(self.my_self, ReceiveTimeout())

    def _ensure_extras(self) -> ActorContextExtras:
        if self._extras is None:
            if self._props is not None:
                context = self._props.context_decorator_chain(self)
            else:
                context = self
            self._extras = ActorContextExtras(context)

        return self._extras


GlobalRootContext = RootContext()
