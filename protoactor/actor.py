from abc import ABCMeta, abstractmethod
from typing import Callable

from . import process_registry, props, context, pid

class Actor(metaclass=ABCMeta):
    @abstractmethod
    async def receive(self, context: context.AbstractContext) -> None:
        pass


def from_producer(producer: Callable[[], Actor]) -> 'Props':
    return props.Props(producer=producer)


def from_func(receive) -> 'Props':
    pass


def spawn(props: 'Props') -> pid.PID:
    return props.spawn(process_registry.ProcessRegistry().next_id())


def spawn_prefix(props: 'Props', prefix: str):
    pass


def spawn_named(props: 'Props', name: str):
    pass


