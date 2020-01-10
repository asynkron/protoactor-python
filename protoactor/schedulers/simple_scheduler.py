import asyncio
from abc import ABCMeta, abstractmethod
from datetime import timedelta

from protoactor.actor import PID
from protoactor.actor.actor_context import AbstractSenderContext, RootContext
from protoactor.actor.cancel_token import CancelToken


class AbstractSimpleScheduler(metaclass=ABCMeta):
    @abstractmethod
    async def schedule_tell_once(self, delay: timedelta, target: PID, message: any) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def schedule_tell_repeatedly(self, delay: timedelta, interval: timedelta, target: PID, message: any,
                                       cancellation_token: CancelToken) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def schedule_request_once(self, delay: timedelta, sender: PID, target: PID,
                                    message: any) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def schedule_request_repeatedly(self, delay: timedelta, interval: timedelta, sender: PID, target: PID,
                                          message: any,
                                          cancellation_token: CancelToken) -> None:
        raise NotImplementedError("Should Implement this method")


class SimpleScheduler(AbstractSimpleScheduler):
    def __init__(self, context: AbstractSenderContext = RootContext()):
        self._context = context

    async def schedule_tell_once(self, delay: timedelta, target: PID, message: any) -> None:
        async def schedule():
            await asyncio.sleep(delay.total_seconds())
            await self._context.send(target, message)

        asyncio.create_task(schedule())

    async def schedule_tell_repeatedly(self, delay: timedelta, interval: timedelta, target: PID, message: any,
                                       cancellation_token: CancelToken) -> None:
        async def schedule():
            await cancellation_token.wait(delay.total_seconds())
            while True:
                if cancellation_token.triggered:
                    return
                await self._context.send(target, message)
                await cancellation_token.wait(interval.total_seconds())

        asyncio.create_task(schedule())

    async def schedule_request_once(self, delay: timedelta, sender: PID, target: PID,
                                    message: any) -> None:
        async def schedule():
            await asyncio.sleep(delay.total_seconds())
            await self._context.request(target, message, sender)

        asyncio.create_task(schedule())

    async def schedule_request_repeatedly(self, delay: timedelta, interval: timedelta, sender: PID, target: PID,
                                          message: any, cancellation_token: CancelToken) -> None:
        async def schedule():
            await cancellation_token.cancellable_wait([], timeout=delay.total_seconds())
            while True:
                if cancellation_token.triggered:
                    return
                await self._context.request(target, message, sender)
                await cancellation_token.cancellable_wait([], timeout=interval.total_seconds())

        asyncio.create_task(schedule())
