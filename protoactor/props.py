from typing import Callable

from .actor import Actor
from .pid import PID

class Props:
    def __init__(self, producer: Callable[[], Actor] = None, spawner: Callable[[str, 'Props', PID], PID] = None ):
        self.__producer = producer
        self.__spawner = spawner

    def with_producer(self, producer: Callable[[], Actor]) -> 'Props':
        pass

    def with_dispatcher(self, producer: Callable[[], Actor]) -> 'Props':
        pass

    def with_middleware(self, *params: Callable[[Actor], Actor]) -> 'Props':
        pass

    def with_mailbox(self, *params: Callable[[Actor], Actor]) -> 'Props':
        pass

    def spawn(self, id: str, parent: PID = None) -> PID:
        return self.__spawner(id, self, parent)