import asyncio
from typing import Any, Awaitable, Sequence, TypeVar, cast, Union

from protoactor.actor.exceptions import OperationCancelled, EventLoopMismatch

_R = TypeVar('_R')


class CancelToken:
    def __init__(self, name: str, loop: asyncio.AbstractEventLoop = None) -> None:
        self.name = name
        self._chain = []
        self._triggered = asyncio.Event(loop=loop)
        self._loop = loop

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def chain(self, token: 'CancelToken') -> 'CancelToken':
        if self.loop != token._loop:
            raise EventLoopMismatch("Chained CancelToken objects must be on the same event loop")
        chain_name = ":".join([self.name, token.name])
        chain = CancelToken(chain_name, loop=self.loop)
        chain._chain.extend([self, token])
        return chain

    def trigger(self) -> None:
        self._triggered.set()

    @property
    def triggered_token(self) -> Union['CancelToken', Any]:
        if self._triggered.is_set():
            return self
        for token in self._chain:
            if token.triggered:
                return token.triggered_token
        return None

    @property
    def triggered(self) -> bool:
        if self._triggered.is_set():
            return True
        return any(token.triggered for token in self._chain)

    def raise_if_triggered(self) -> None:
        if self.triggered:
            raise OperationCancelled(
                "Cancellation requested by {} token".format(self.triggered_token))

    async def wait(self) -> None:
        if self.triggered_token is not None:
            return

        futures = [asyncio.ensure_future(self._triggered.wait(), loop=self.loop)]
        for token in self._chain:
            futures.append(asyncio.ensure_future(token.wait(), loop=self.loop))

        def cancel_not_done(fut: 'asyncio.Future[None]') -> None:
            for future in futures:
                if not future.done():
                    future.cancel()

        async def _wait_for_first(futures: Sequence[Awaitable[Any]]) -> None:
            for future in asyncio.as_completed(futures):
                await cast(Awaitable[Any], future)
                return

        fut = asyncio.ensure_future(_wait_for_first(futures), loop=self.loop)
        fut.add_done_callback(cancel_not_done)
        await fut

    async def cancellable_wait(self, *awaitables: Awaitable[_R], timeout: float = None) -> _R:
        futures = [asyncio.ensure_future(a, loop=self.loop) for a in awaitables + (self.wait(),)]
        try:
            done, pending = await asyncio.wait(
                futures,
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED,
                loop=self.loop,
            )
        except asyncio.futures.CancelledError:
            for future in futures:
                future.cancel()
            raise
        for task in pending:
            task.cancel()
        await asyncio.wait(pending, return_when=asyncio.ALL_COMPLETED, loop=self.loop,)
        if not done:
            raise TimeoutError()
        if self.triggered_token is not None:
            for task in done:
                task.exception()
            raise OperationCancelled("Cancellation requested by {} token".format(self.triggered_token))
        return done.pop().result()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return '<CancelToken: {0}>'.format(self.name)
