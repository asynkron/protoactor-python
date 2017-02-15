from abc import ABCMeta, abstractmethod
from typing import Callable

from .props import Props
from .context import Context
from .pid import PID

class Actor(metaclass=ABCMeta):
    @abstractmethod
    async def receive(self, context: Context):
        pass


def from_producer(producer: Callable[[], Actor]) -> Props:
    return Props(producer=producer)


def from_func(receive) -> Props:
    pass


def spawn(props: Props) -> PID:
    pass


def spawn_prefix(props, prefix: str):
    pass


def spawn_named(props, name: str):
    pass


