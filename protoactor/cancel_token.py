import asyncio
from typing import List

class BaseCancelTokenException(Exception):
    """
    Base exception class for the `asyncio-cancel-token` library.
    """
    pass


class EventLoopMismatch(BaseCancelTokenException):
    """
    Raised when two different asyncio event loops are referenced, but must be equal
    """
    pass


class OperationCancelled(BaseCancelTokenException):
    """
    Raised when an operation was cancelled.
    """
    pass


class CancelToken:
    def __init__(self, name: str, loop: asyncio.AbstractEventLoop = None) -> None:
        self.name = name
        self._chain: List['CancelToken'] = []
        self._triggered = asyncio.Event(loop=loop)
        self._loop = loop

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def trigger(self) -> None:
        self._triggered.set()

    @property
    def triggered(self) -> bool:
        return self._triggered.is_set()

    def raise_if_triggered(self) -> None:
        if self.triggered:
            raise OperationCancelled()

    async def wait(self) -> None:
        await self._triggered.wait()

    async def cancellable_wait(self, fut: asyncio.Future, timeout: float = None):
        done, pending = await asyncio.wait([fut], timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
        if not done:
            fut.cancel()
            raise TimeoutError()
        return done.pop().result()