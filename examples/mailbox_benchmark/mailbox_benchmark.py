import asyncio
import cProfile
from typing import Callable

from protoactor.actor.actor_context import AbstractContext, GlobalRootContext
from protoactor.actor.props import Props
from protoactor.mailbox.mailbox import AbstractMailbox, DefaultMailbox
from protoactor.mailbox.queue import UnboundedMailboxQueue


async def process_message(ctx: AbstractContext):
    if isinstance(ctx.message, str):
        await ctx.respond('done')


async def run_test(mailbox: Callable[..., AbstractMailbox]):
    props = Props.from_func(process_message) \
                 .with_mailbox(mailbox)

    pid = GlobalRootContext.spawn(props)
    for i in range(10000):
        await GlobalRootContext.send(pid, i)
    await GlobalRootContext.request_future(pid, 'stop')


async def main():
    pr = cProfile.Profile()

    pr.enable()
    await run_test(lambda: DefaultMailbox(UnboundedMailboxQueue(), UnboundedMailboxQueue(), []))
    pr.disable()

    pr.print_stats(sort='time')


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
