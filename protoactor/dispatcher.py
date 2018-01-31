import asyncio
from abc import ABCMeta, abstractmethod
from threading import Thread
from typing import Callable


class AbstractMessageInvoker(metaclass=ABCMeta):
    @abstractmethod
    async def invoke_system_message(self, msg: object):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def invoke_user_message(self, msg: object):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def escalate_failure(self, reason: Exception, msg: object):
        raise NotImplementedError("Should Implement this method")


class AbstractDispatcher(metaclass=ABCMeta):
    @property
    @abstractmethod
    def throughput(self) -> int:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def schedule(self, runner: Callable[..., asyncio.Task]):
        raise NotImplementedError("Should Implement this method")


def _run_async(runner):
    async_loop = asyncio.new_event_loop()
    async_loop.run_until_complete(runner())
    async_loop.close()

class ThreadDispatcher(AbstractDispatcher):
    @property
    def throughput(self) -> int:
        return 300

    def schedule(self, runner: Callable[..., asyncio.Task]):
        t = Thread(target=_run_async, args=(runner,))
        t.start()
