import asyncio
import logging
import threading
from datetime import timedelta

import pytest

from protoactor.actor.actor import RootContext, Actor, AbstractContext
from protoactor.actor.props import Props
from protoactor.router.messages import RemoveRoutee, GetRoutees, AddRoutee, BroadcastMessage
from protoactor.router.router import Router

context = RootContext()
timeout = timedelta(milliseconds=1000)
my_actor_props = Props.from_producer(lambda: MyTestActor())


@pytest.mark.asyncio
async def test_broadcast_group_router_all_routees_receive_messages():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await context.send(router, 'hello')

    assert await context.request_async(routee1, 'received?', timeout) == 'hello'
    assert await context.request_async(routee2, 'received?', timeout) == 'hello'
    assert await context.request_async(routee3, 'received?', timeout) == 'hello'


@pytest.mark.asyncio
async def test_broadcast_group_router_when_one_routee_is_stopped_all_other_routees_receive_messages():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await routee2.stop()
    await context.send(router, 'hello')

    assert await context.request_async(routee1, 'received?', timeout) == 'hello'
    assert await context.request_async(routee3, 'received?', timeout) == 'hello'


@pytest.mark.asyncio
async def test_broadcast_group_router_when_one_routee_is_slow_all_other_routees_receive_messages():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await context.send(routee2, 'go slow')
    await context.send(router, 'hello')

    assert await context.request_async(routee1, 'received?', timeout) == 'hello'
    assert await context.request_async(routee3, 'received?', timeout) == 'hello'


@pytest.mark.asyncio
async def test_broadcast_group_router_routees_can_be_removed():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await context.send(router, RemoveRoutee(routee1))

    routees = await context.request_async(router, GetRoutees(), timeout)
    assert routee1 not in routees.pids
    assert routee2 in routees.pids
    assert routee3 in routees.pids


@pytest.mark.asyncio
async def test_broadcast_group_router_routees_can_be_added():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()
    routee4 = context.spawn(my_actor_props)

    await context.send(router, AddRoutee(routee4))

    routees = await context.request_async(router, GetRoutees(), timeout)
    assert routee1 in routees.pids
    assert routee2 in routees.pids
    assert routee3 in routees.pids
    assert routee4 in routees.pids


@pytest.mark.asyncio
async def test_broadcast_group_router_removed_routees_no_longer_receive_messages():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await context.send(router, 'first message')
    await context.send(router, RemoveRoutee(routee1))
    await context.send(router, 'second message')

    assert await context.request_async(routee1, 'received?', timeout) == 'first message'
    assert await context.request_async(routee2, 'received?', timeout) == 'second message'
    assert await context.request_async(routee3, 'received?', timeout) == 'second message'


@pytest.mark.asyncio
async def test_broadcast_group_router_added_routees_receive_messages():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()
    routee4 = context.spawn(my_actor_props)

    await context.send(router, AddRoutee(routee4))
    await context.send(router, 'a message')

    assert await context.request_async(routee1, 'received?', timeout) == 'a message'
    assert await context.request_async(routee2, 'received?', timeout) == 'a message'
    assert await context.request_async(routee3, 'received?', timeout) == 'a message'
    assert await context.request_async(routee4, 'received?', timeout) == 'a message'

@pytest.mark.asyncio
async def test_broadcast_group_router_all_routees_receive_router_broadcast_messages():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await context.send(router, BroadcastMessage('hello'))

    assert await context.request_async(routee1, 'received?', timeout) == 'hello'
    assert await context.request_async(routee2, 'received?', timeout) == 'hello'
    assert await context.request_async(routee3, 'received?', timeout) == 'hello'


def create_broadcast_group_router_with3_routees():
    routee1 = context.spawn(my_actor_props)
    routee2 = context.spawn(my_actor_props)
    routee3 = context.spawn(my_actor_props)

    props = Router.new_broadcast_group([routee1, routee2, routee3])
    router = context.spawn(props)
    return router, routee1, routee2, routee3


class MyTestActor(Actor):
    def __init__(self):
        self._received = None

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if msg == 'received?':
            await context.respond(self._received)
        elif msg == 'go slow':
            await asyncio.sleep(5000)
        elif isinstance(msg, str):
            self._received = msg
