import asyncio
import threading
from typing import Callable
from threading import Thread
from abc import ABCMeta, abstractmethod
from protoactor.actor.utils import Singleton


class AbstractMessageInvoker(metaclass=ABCMeta):
    @abstractmethod
    def invoke_system_message(self, msg: object):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def invoke_user_message(self, msg: object):
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
    def schedule(self, runner: Callable[..., asyncio.coroutine], **kwargs: ...):
        raise NotImplementedError("Should Implement this method")


class Dispatchers(metaclass=Singleton):
    @property
    def default_dispatcher(self) -> AbstractDispatcher:
        return ThreadDispatcher()

    @property
    def synchronous_dispatcher(self) -> AbstractDispatcher:
        return SynchronousDispatcher()


class ThreadDispatcher(AbstractDispatcher):
    def __init__(self, async_loop=None):
        self.async_loop = async_loop

    @property
    def throughput(self) -> int:
        return 300

    def schedule(self, runner: Callable[..., asyncio.coroutine], **kwargs: ...):
        t = Thread(target=self.__run_async, daemon=True, args=(runner, self.async_loop), kwargs=kwargs)
        t.start()

    def __run_async(self, runner, async_loop, **kwargs):
        async_loop_absent = async_loop is None
        try:
            if async_loop_absent:
                async_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(async_loop)
            async_loop.run_until_complete(runner(**kwargs))
        finally:
            if async_loop_absent:
                async_loop.close()


class SynchronousDispatcher(AbstractDispatcher):
    def __init__(self, async_loop=None):
        self.async_loop = async_loop

    @property
    def throughput(self) -> int:
        return 300

    def schedule(self, runner: Callable[..., asyncio.coroutine], **kwargs: ...):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        thread = threading.Thread(target=loop.run_forever, daemon=True)
        thread.start()

        future = asyncio.run_coroutine_threadsafe(runner(**kwargs), loop)
        future.result()

        loop.call_soon_threadsafe(loop.stop)
        thread.join()
