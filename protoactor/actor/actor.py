from abc import abstractmethod

from protoactor.actor.actor_context import AbstractContext


class Actor():
    @abstractmethod
    async def receive(self, context: AbstractContext) -> None:
        pass


class EmptyActor(Actor):
    def __init__(self, receive):
        self._receive = receive

    async def receive(self, context: AbstractContext):
        await self._receive(context)
