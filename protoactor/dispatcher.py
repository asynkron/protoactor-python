from abc import ABCMeta, abstractmethod, abstractproperty
import asyncio
from multiprocessing import Process
from threading import Thread
from typing import Callable


class AbstractDispatcher(metaclass=ABCMeta):
    @property
    @abstractproperty
    def throughput(self) -> int:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def schedule(self, runner: Callable[..., asyncio.Task]):
        raise NotImplementedError("Should Implement this method")

def _run_async(runner):
    async_loop = asyncio.new_event_loop()
    # task = asyncio.wait(async_loop.create_task(runner()))
    async_loop.run_until_complete(runner())
    async_loop.close()

class ProcessDispatcher(AbstractDispatcher):
    @property
    def throughput(self) -> int:
        return 300

    def schedule(self, runner: Callable[..., asyncio.Task]):
        p = Process(target=_run_async, args=(runner,))
        p.start()

class ThreadDispatcher(AbstractDispatcher):
    @property
    def throughput(self) -> int:
        return 300

    def schedule(self, runner: Callable[..., asyncio.Task]):
        p = Thread(target=_run_async, args=(runner,))
        p.run()
