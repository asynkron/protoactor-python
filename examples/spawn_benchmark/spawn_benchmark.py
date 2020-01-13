import asyncio
import cProfile
from dataclasses import dataclass
from typing import Optional

from protoactor.actor import PID
from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import RootContext, AbstractContext, GlobalRootContext
from protoactor.actor.props import Props


@dataclass
class Request:
    div: int
    num: int
    size: int


class MyActor(Actor):
    def __init__(self):
        self._replies: Optional[int] = None
        self._reply_to: Optional[PID] = None
        self._sum: int = 0

    async def receive(self, context: AbstractContext):
        msg = context.message
        if isinstance(msg, Request):
            if msg.size == 1:
                await context.respond(msg.num)
                await context.stop(context.my_self)
                return

            self._replies = msg.div
            self._reply_to = context.sender

            for i in range(msg.div):
                child = GlobalRootContext.spawn(props)
                await context.request(child, Request(num=msg.num + i * (msg.size // msg.div),
                                                     size=msg.size // msg.div,
                                                     div=msg.div))
        elif isinstance(msg, int):
            self._sum += msg
            self._replies -= 1
            if self._replies == 0:
                await context.send(self._reply_to, self._sum)


props = Props.from_producer(MyActor)


async def main():
    context = RootContext()
    pr = cProfile.Profile()
    while True:
        pid = context.spawn(props)
        pr.clear()
        pr.enable()
        response = await context.request_future(pid, Request(num=0,
                                                             size=100,
                                                             div=10))
        pr.disable()
        pr.print_stats(sort='time')
        print(response)
        await context.stop_future(pid)
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())
