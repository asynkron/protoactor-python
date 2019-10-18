import asyncio

from protoactor.actor.actor import Actor, AbstractContext, RootContext
from protoactor.actor.props import Props
from protoactor.router.messages import AbstractHashable
from protoactor.router.router import Router

my_actor_props = Props.from_producer(lambda: MyTestActor())


class Message(AbstractHashable):
    def __init__(self, text: str):
        self.text = text

    def hash_by(self) -> str:
        return self.text

    def __str__(self):
        return self.text


class MyTestActor(Actor):
    def __init__(self):
        self._received_messages = []

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if isinstance(msg, Message):
            print('actor %s got message %s' % (str(context.my_self.id), msg.text))


async def run_broadcast_pool_test():
    context = RootContext()
    props = Router.new_broadcast_pool(my_actor_props, 5)

    for i in range(10):
        pid = context.spawn(props)
        await context.send(pid, Message('%s' % (i % 4)))


async def run_broadcast_group_test():
    context = RootContext()
    props = Router.new_broadcast_group([context.spawn(my_actor_props),
                                        context.spawn(my_actor_props),
                                        context.spawn(my_actor_props),
                                        context.spawn(my_actor_props)])

    for i in range(10):
        pid = context.spawn(props)
        await context.send(pid, Message('%s' % (i % 4)))


async def run_random_pool_test():
    context = RootContext()
    props = Router.new_random_pool(my_actor_props, 5)
    pid = context.spawn(props)

    for i in range(10):
        await context.send(pid, Message('%s' % (i % 4)))


async def run_random_group_test():
    context = RootContext()
    props = Router.new_random_group([context.spawn(my_actor_props),
                                     context.spawn(my_actor_props),
                                     context.spawn(my_actor_props),
                                     context.spawn(my_actor_props)])

    pid = context.spawn(props)
    for i in range(10):
        await context.send(pid, Message('%s' % (i % 4)))


async def run_round_robin_pool_test():
    context = RootContext()
    props = Router.new_round_robin_pool(my_actor_props, 5)
    pid = context.spawn(props)

    for i in range(10):
        await context.send(pid, Message('%s' % (i % 4)))


async def run_round_robin_group_test():
    context = RootContext()
    props = Router.new_round_robin_group([context.spawn(my_actor_props),
                                          context.spawn(my_actor_props),
                                          context.spawn(my_actor_props),
                                          context.spawn(my_actor_props)])

    pid = context.spawn(props)
    for i in range(10):
        await context.send(pid, Message('%s' % (i % 4)))


async def run_consistent_hash_pool_test():
    context = RootContext()
    props = Router.new_consistent_hash_pool(my_actor_props, 5)
    pid = context.spawn(props)

    for i in range(10):
        await context.send(pid, Message('%s' % (i % 4)))


async def run_consistent_hash_group_test():
    context = RootContext()
    props = Router.new_consistent_hash_group([context.spawn(my_actor_props),
                                              context.spawn(my_actor_props),
                                              context.spawn(my_actor_props),
                                              context.spawn(my_actor_props)])

    pid = context.spawn(props)
    for i in range(10):
        await context.send(pid, Message('%s' % (i % 4)))


async def main():
    await run_broadcast_pool_test()
    # await run_broadcast_group_test()

    #await run_random_pool_test()
    # await run_random_group_test()

    # await run_round_robin_pool_test()
    # await run_round_robin_group_test()

    # await run_consistent_hash_pool_test()
    # await run_consistent_hash_group_test()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
