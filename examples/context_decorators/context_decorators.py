import asyncio
from datetime import timedelta

from protoactor.actor import PID
from protoactor.actor.actor_context import AbstractRootContext, AbstractContext, RootContext
from protoactor.actor.cancel_token import CancelToken
from protoactor.actor.context_decorator import RootContextDecorator, ActorContextDecorator
from protoactor.actor.props import Props


class LoggingRootDecorator(RootContextDecorator):
    def __init__(self, context: AbstractRootContext):
        super().__init__(context)

    async def request_future(self, target: PID, message: object, timeout: timedelta = None,
                             cancellation_token: CancelToken = None) -> asyncio.Future:
        print('Enter request future')
        res = await super().request_future(target, message)
        print('Exit request future')
        return res


class LoggingDecorator(ActorContextDecorator):
    def __init__(self, context: AbstractContext, logger_name: str):
        super().__init__(context)
        self._logger_name = logger_name

    async def respond(self, message: object):
        print(f'{self._logger_name} : Enter respond')
        await super().respond(message)
        print(f'{self._logger_name} : Exit respond')


async def main():
    context = LoggingRootDecorator(RootContext())

    async def fn(context: AbstractContext):
        message = context.message
        if isinstance(message, str):
            print(f'Inside Actor: {message}')
            await context.respond("Yo!")

    props = Props.from_func(fn).with_context_decorator([lambda c: LoggingDecorator(c, 'logger1'),
                                                        lambda c: LoggingDecorator(c, 'logger2')])
    pid = context.spawn(props)

    res = await context.request_future(pid, 'Hello')
    print(f'Got result {res}')
    input()


if __name__ == "__main__":
    asyncio.run(main())
