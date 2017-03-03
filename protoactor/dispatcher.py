from abc import ABCMeta, abstractmethod, abstractproperty
import asyncio
from multiprocessing import Process
from typing import Callable


class AbstractDispatcher(metaclass=ABCMeta):
    @property
    @abstractproperty
    def throughput(self) -> int:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def schedule(self, runner: Callable[..., asyncio.Task]):
        raise NotImplementedError("Should Implement this method")


class ProcessDispatcher(AbstractDispatcher):
    @property
    def throughput(self) -> int:
        raise NotImplementedError("Should Implement this method")

    def schedule(self, runner: Callable[..., asyncio.Task]):
        def run_async(runner):
            async_loop = asyncio.get_event_loop()
            task = asyncio.wait(async_loop.create_task(runner()))
            async_loop.run_until_complete(task)
            async_loop.close()

        p = Process(target=run_async, args=runner)
        p.start()
