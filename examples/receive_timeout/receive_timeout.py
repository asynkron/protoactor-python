import asyncio
import itertools
from datetime import timedelta, datetime

from protoactor.actor.actor_context import RootContext, AbstractContext
from protoactor.actor.messages import Started, ReceiveTimeout, AbstractNotInfluenceReceiveTimeout
from protoactor.actor.props import Props


class NoInfluence(AbstractNotInfluenceReceiveTimeout):
    pass


async def main():
    root_context = RootContext()
    counter = itertools.count()
    next(counter)

    async def fn(context: AbstractContext):
        msg = context.message
        if isinstance(msg, Started):
            print(f'{datetime.today().strftime("%Y-%m-%d-%H.%M.%S")} Started')
            context.set_receive_timeout(timedelta(seconds=1))
        elif isinstance(msg, ReceiveTimeout):
            print(f'{datetime.today().strftime("%Y-%m-%d-%H.%M.%S")} ReceiveTimeout: {next(counter)}')
        elif isinstance(msg, NoInfluence):
            print(f'{datetime.today().strftime("%Y-%m-%d-%H.%M.%S")} Received a no-influence message')
        elif isinstance(msg, str):
            print(f'{datetime.today().strftime("%Y-%m-%d-%H.%M.%S")} Received message: {msg}')

    props = Props.from_func(fn)
    pid = root_context.spawn(props)

    for i in range(6):
        await root_context.send(pid, 'hello')
        await asyncio.sleep(0.5)

    print('Hit [return] to send no-influence messages')
    input()

    for i in range(6):
        await root_context.send(pid, NoInfluence())
        await asyncio.sleep(0.5)

    print('Hit [return] to send a message to cancel the timeout')
    input()

    await root_context.send(pid, 'cancel')

    print('Hit [return] to finish')
    input()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
