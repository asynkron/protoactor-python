import asyncio
from abc import ABCMeta, abstractmethod
from threading import Thread
from typing import Callable


class AbstractDispatcher(metaclass=ABCMeta):
    @property
    @abstractmethod
    def throughput(self) -> int:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def schedule(self, runner: Callable[..., asyncio.Task]):
        raise NotImplementedError("Should Implement this method")


def _run_async(runner, async_loop):
    async_loop_absent = async_loop is None

    try:
        if async_loop_absent:
            async_loop = asyncio.new_event_loop()
        async_loop.run_until_complete(runner())
    finally:
        if async_loop_absent:
            async_loop.close()

class ThreadDispatcher(AbstractDispatcher):
    def __init__(self, async_loop=None):
        self.async_loop = async_loop

    @property
    def throughput(self) -> int:
        return 300

    def schedule(self, runner: Callable[..., asyncio.Task]):
        t = Thread(target=_run_async, args=(runner, self.async_loop))
        t.start()
