import asyncio
from datetime import timedelta
from typing import Optional

from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import AbstractContext, RootContext
from protoactor.actor.cancel_token import CancelToken
from protoactor.actor.messages import Started
from protoactor.actor.props import Props
from protoactor.schedulers.simple_scheduler import SimpleScheduler


class Hello:
    pass


class HickUp:
    pass


class AbortHickUp:
    pass


class Greet:
    def __init__(self, who: str):
        self._who = who

    def who(self) -> str:
        return self._who


class SimpleMessage:
    def __init__(self, msg: str):
        self._msg = msg

    def msg(self) -> str:
        return self._msg


class ScheduleGreetActor(Actor):
    def __init__(self):
        pass

    async def receive(self, context: AbstractContext):
        msg = context.message
        if isinstance(msg, Greet):
            print(f"Hi {msg.who()}")
            await context.respond(Greet('Roger'))


class ScheduleActor(Actor):
    def __init__(self):
        self._scheduler: SimpleScheduler = SimpleScheduler()
        self._timer: CancelToken = CancelToken('')
        self._counter: int = 0

    async def receive(self, context: AbstractContext):
        msg = context.message
        if isinstance(msg, Started):
            pid = context.spawn(Props.from_producer(ScheduleGreetActor))
            await self._scheduler.schedule_tell_once(timedelta(milliseconds=100), context.my_self,
                                                     SimpleMessage('test 1'))
            await self._scheduler.schedule_tell_once(timedelta(milliseconds=200), context.my_self,
                                                     SimpleMessage('test 2'))
            await self._scheduler.schedule_tell_once(timedelta(milliseconds=300), context.my_self,
                                                     SimpleMessage('test 3'))
            await self._scheduler.schedule_tell_once(timedelta(milliseconds=400), context.my_self,
                                                     SimpleMessage('test 4'))
            await self._scheduler.schedule_tell_once(timedelta(milliseconds=500), context.my_self,
                                                     SimpleMessage('test 5'))
            await self._scheduler.schedule_request_once(timedelta(seconds=1), context.my_self, pid,
                                                     Greet('Daniel'))
            await self._scheduler.schedule_tell_once(timedelta(seconds=5), context.my_self,
                                                     Hello())
        elif isinstance(msg, Hello):
            print("Hello Once, let's give you a hickup every 0.5 second starting in 3 seconds!")
            await self._scheduler.schedule_tell_repeatedly(timedelta(seconds=3), timedelta(milliseconds=500),
                                                           context.my_self, HickUp(), self._timer)
        elif isinstance(msg, HickUp):
            self._counter += 1
            print('Hello!')
            if self._counter == 5:
                self._timer.trigger()
                await context.send(context.my_self, AbortHickUp())
        elif isinstance(msg, AbortHickUp):
            print(f'Aborted hickup after {self._counter} times')
            print('All this was scheduled calls, have fun!')
        elif isinstance(msg, Greet):
            print(f'Thanks {msg.who()}')
        elif isinstance(msg, SimpleMessage):
            print(msg.msg())


async def main():
    context = RootContext()
    props = Props.from_producer(ScheduleActor)
    pid = context.spawn(props)

    input()

if __name__ == "__main__":
    asyncio.run(main())
