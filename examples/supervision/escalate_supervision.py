import asyncio

from protoactor.actor.actor_context import AbstractContext, RootContext
from protoactor.actor.messages import Started
from protoactor.actor.props import Props
from protoactor.actor.protos_pb2 import Terminated
from protoactor.actor.supervision import OneForOneStrategy, SupervisorDirective


async def main():
    async def child_fn(context: AbstractContext):
        print(f'{context.my_self.id}: MSG: {type(context.message)}')
        if isinstance(context.message, Started):
            raise Exception('child failure')

    child_props = Props.from_func(child_fn)

    async def root_fn(context: AbstractContext):
        print(f'{context.my_self.id}: MSG: {type(context.message)}')
        if isinstance(context.message, Started):
            context.spawn_named(child_props, 'child')
        elif isinstance(context.message, Terminated):
            print(f'Terminated {context.message.who}')

    root_props = Props.from_func(root_fn).with_child_supervisor_strategy(
        OneForOneStrategy(lambda pid, reason: SupervisorDirective.Escalate, 0, None))

    root_context = RootContext()
    root_context.spawn_named(root_props, 'root')

    input()

if __name__ == "__main__":
    asyncio.run(main())
