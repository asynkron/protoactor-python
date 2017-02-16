from abc import ABCMeta, abstractmethod
from typing import Callable

from .process_registry import ProcessRegistry
from .props import Props
from .context import AbstractContext
from .pid import PID

class Actor(metaclass=ABCMeta):
    @abstractmethod
    async def receive(self, context: AbstractContext):
        pass


def from_producer(producer: Callable[[], Actor]) -> Props:
    return Props(producer=producer)


def from_func(receive) -> Props:
    pass


def spawn(props: Props) -> PID:
    return props.spawn(ProcessRegistry().next_id())


def spawn_prefix(props, prefix: str):
    pass


def spawn_named(props, name: str):
    pass


