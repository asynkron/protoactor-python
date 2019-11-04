import asyncio
from asyncio.futures import Future
from asyncio.tasks import Task
from datetime import timedelta
from typing import Callable

from protoactor.actor import PID
from protoactor.actor.actor_context import AbstractRootContext, AbstractContext
from protoactor.actor.cancel_token import CancelToken
from protoactor.actor.message_envelope import MessageEnvelope
from protoactor.actor.message_header import MessageHeader
from protoactor.actor.props import Props

is_import = False
if is_import:
    from protoactor.actor.actor import Actor

class RootContextDecorator(AbstractRootContext):
    def __init__(self, context: AbstractRootContext):
        self._context = context

    @property
    def headers(self) -> MessageHeader:
        return self._context.headers

    @property
    def message(self) -> any:
        return self._context.message

    def spawn(self, props: 'Props') -> PID:
        return self._context.spawn(props)

    def spawn_named(self, props: 'Props', name: str) -> PID:
        return self._context.spawn_named(props, name)

    def spawn_prefix(self, props: 'Props', prefix: str) -> PID:
        return self._context.spawn_prefix(props, prefix)

    async def send(self, target: PID, message: any) -> None:
        await self._context.send(target, message)

    async def request(self, target: PID, message: any) -> None:
        await self._context.request(target, message)

    async def request_future(self, target: PID, message: object, timeout: timedelta = None,
                             cancellation_token: CancelToken = None) -> asyncio.Future:
        return await self._context.request_future(target, message, timeout, cancellation_token)

    async def stop(self, pid: PID) -> None:
        await self._context.stop(pid)

    async def stop_future(self, pid: PID) -> asyncio.Future:
        return await self._context.stop_future(pid)

    async def poison(self, pid: PID) -> None:
        await self._context.poison(pid)

    async def poison_future(self, pid: PID) -> asyncio.Future:
        return await self._context.poison_future(pid)


class ActorContextDecorator(AbstractContext):
    def __init__(self, context: AbstractContext):
        self._context = context

    @property
    def headers(self) -> MessageHeader:
        return self._context.headers

    @property
    def message(self) -> any:
        return self._context.message

    @property
    def parent(self) -> PID:
        return self._context.parent

    @property
    def my_self(self) -> PID:
        return self._context.my_self

    @property
    def sender(self) -> PID:
        return self._context.sender

    @property
    def actor(self) -> 'Actor':
        return self._context.actor

    @property
    def receive_timeout(self) -> timedelta:
        return self._context.receive_timeout

    @property
    def children(self):
        return self._context.children

    @property
    def stash(self):
        return self._context.stash

    async def send(self, target: PID, message: any) -> None:
        await self._context.send(target, message)

    async def request(self, target: PID, message: any) -> None:
        await self._context.request(target, message)

    async def request_future(self, target: PID, message: object, timeout: timedelta = None,
                             cancellation_token: CancelToken = None) -> asyncio.Future:
        return await self._context.request_future(target, message, timeout, cancellation_token)

    async def receive(self, envelope: MessageEnvelope):
        return await self._context.receive(envelope)

    async def respond(self, message: object):
        return await self._context.respond(message)

    def spawn(self, props: 'Props') -> PID:
        return self._context.spawn(props)

    def spawn_named(self, props: 'Props', name: str) -> PID:
        return self._context.spawn_named(props, name)

    def spawn_prefix(self, props: 'Props', prefix: str) -> PID:
        return self._context.spawn_prefix(props, prefix)

    async def watch(self, pid: PID) -> None:
        await self._context.watch(pid)

    async def unwatch(self, pid: PID) -> None:
        await self._context.unwatch(pid)

    def set_receive_timeout(self, receive_timeout: timedelta) -> None:
        self._context.set_receive_timeout(receive_timeout)

    def cancel_receive_timeout(self) -> None:
        self._context.cancel_receive_timeout()

    async def forward(self, target: PID) -> None:
        await self._context.forward(target)

    def reenter_after(self, target: Task, action: Callable) -> None:
        self._context.reenter_after(target, action)

    async def stop(self, pid: PID) -> None:
        pass

    async def stop_future(self, pid: PID) -> Future:
        pass

    async def poison(self, pid: PID) -> None:
        pass

    async def poison_future(self, pid: PID) -> Future:
        pass
