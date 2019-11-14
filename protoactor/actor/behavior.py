import asyncio

from protoactor.actor.actor_context import AbstractContext
from protoactor.actor.utils import Stack


class Behavior:
    def __init__(self, receive: asyncio.Future = None) -> None:
        self._behaviors = Stack()
        self.become(receive)

    def become(self, receive: object):
        self._behaviors.clear()
        self._behaviors.push(receive)

    def become_stacked(self, receive: object):
        self._behaviors.push(receive)

    def unbecome_stacked(self) -> None:
        self._behaviors.pop()

    def receive_async(self, context: AbstractContext) -> asyncio.Future:
        behavior = self._behaviors.peek()
        return behavior(context)
