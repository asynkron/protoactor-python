from datetime import timedelta

import pytest

from protoactor.actor.actor_context import RootContext, Actor, AbstractContext
from protoactor.actor.props import Props
from protoactor.router.messages import RemoveRoutee, GetRoutees, AddRoutee, BroadcastMessage
from protoactor.router.router import Router
from tests.test_fixtures.test_mailbox import MockMailbox

context = RootContext()
timeout = timedelta(milliseconds=1000)
my_actor_props = Props.from_producer(lambda: MyTestActor()).with_mailbox(MockMailbox)


@pytest.mark.asyncio
async def test_round_robin_group_router_routees_receive_messages_in_round_robin_style():
    router, routee1, routee2, routee3 = create_router_with3_routees()

    await context.send(router, '1')

    # only routee1 has received the message
    assert await context.request_future(routee1, 'received?', timeout) == '1'
    assert await context.request_future(routee2, 'received?', timeout) is None
    assert await context.request_future(routee3, 'received?', timeout) is None

    await context.send(router, '2')
    await context.send(router, '3')

    # routees 2 and 3 receive next messages
    assert await context.request_future(routee1, 'received?', timeout) == '1'
    assert await context.request_future(routee2, 'received?', timeout) == '2'
    assert await context.request_future(routee3, 'received?', timeout) == '3'

    await context.send(router, '4')

    # Round robin kicks in and routee1 recevies next message
    assert await context.request_future(routee1, 'received?', timeout) == '4'
    assert await context.request_future(routee2, 'received?', timeout) == '2'
    assert await context.request_future(routee3, 'received?', timeout) == '3'


@pytest.mark.asyncio
async def test_round_robin_group_router_routees_can_be_removed():
    router, routee1, routee2, routee3 = create_router_with3_routees()

    await context.send(router, RemoveRoutee(routee1))

    routees = await context.request_future(router, GetRoutees(), timeout)
    assert routee1 not in routees.pids
    assert routee2 in routees.pids
    assert routee3 in routees.pids


@pytest.mark.asyncio
async def test_round_robin_group_router_routees_can_be_added():
    router, routee1, routee2, routee3 = create_router_with3_routees()
    routee4 = context.spawn(my_actor_props)
    await context.send(router, AddRoutee(routee4))

    routees = await context.request_future(router, GetRoutees(), timeout)
    assert routee1 in routees.pids
    assert routee2 in routees.pids
    assert routee3 in routees.pids
    assert routee4 in routees.pids


@pytest.mark.asyncio
async def test_round_robin_group_router_removed_routees_no_longer_receive_messages():
    router, routee1, routee2, routee3 = create_router_with3_routees()

    await context.send(router, '0')
    await context.send(router, '0')
    await context.send(router, '0')
    await context.send(router, RemoveRoutee(routee1))
    # we should have 2 routees, so send 3 messages to ensure round robin happens
    await context.send(router, '3')
    await context.send(router, '3')
    await context.send(router, '3')

    assert await context.request_future(routee1, 'received?', timeout) == '0'
    assert await context.request_future(routee2, 'received?', timeout) == '3'
    assert await context.request_future(routee3, 'received?', timeout) == '3'


@pytest.mark.asyncio
async def test_round_robin_group_router_all_routees_receive_router_broadcast_messages():
    router, routee1, routee2, routee3 = create_router_with3_routees()

    await context.send(router, BroadcastMessage('hello'))

    assert await context.request_future(routee1, 'received?', timeout) == 'hello'
    assert await context.request_future(routee2, 'received?', timeout) == 'hello'
    assert await context.request_future(routee3, 'received?', timeout) == 'hello'


def create_router_with3_routees():
    routee1 = context.spawn(my_actor_props)
    routee2 = context.spawn(my_actor_props)
    routee3 = context.spawn(my_actor_props)

    props = Router.new_round_robin_group([routee1, routee2, routee3]) \
        .with_mailbox(MockMailbox)

    router = context.spawn(props)
    return router, routee1, routee2, routee3


class MyTestActor(Actor):
    def __init__(self):
        self._received = None

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if msg == 'received?':
            await context.respond(self._received)
        elif isinstance(msg, str):
            self._received = msg
