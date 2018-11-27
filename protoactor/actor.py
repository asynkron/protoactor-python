from abc import ABCMeta, abstractmethod
from typing import Callable

from protoactor.props import Props
from .protos_pb2 import PID

from . import process_registry, props, context


class Actor(metaclass=ABCMeta):
    @abstractmethod
    async def receive(self, context: context.AbstractContext) -> None:
        pass


class EmptyActor(Actor):
    def __init__(self, receive):
        self._receive = receive

    async def receive(self, context):
        await self._receive(context)


def from_producer(producer: Callable[[], Actor]) -> 'Props':
    return props.Props(producer=producer)


def from_func(receive) -> 'Props':
    return from_producer(lambda: EmptyActor(receive))


def spawn(props: 'Props') -> PID:
    return props.spawn(process_registry.ProcessRegistry().next_id())


def spawn_prefix(props: 'Props', prefix: str):
    pass


def spawn_named(props: 'Props', name: str):
    pass
