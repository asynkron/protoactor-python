import asyncio

from protoactor.actor.actor import AbstractContext
from protoactor.actor.utils import Stack


class Behavior:
    def __init__(self, receive: asyncio.Future = None) -> None:
        self.__behaviors = Stack()
        self.become(receive)

    def become(self, receive: object):
        self.__behaviors.clear()
        self.__behaviors.push(receive)

    def become_stacked(self, receive: object):
        self.__behaviors.push(receive)

    def unbecome_stacked(self) -> None:
        self.__behaviors.pop()

    def receive_async(self, context: AbstractContext) -> asyncio.Future:
        behavior = self.__behaviors.peek()
        return behavior(context)
