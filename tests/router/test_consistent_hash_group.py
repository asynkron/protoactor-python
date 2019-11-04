import uuid
from datetime import timedelta

import pytest

from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import RootContext, AbstractContext
from protoactor.actor.props import Props
from protoactor.router.messages import AbstractHashable, AddRoutee, RemoveRoutee, GetRoutees, BroadcastMessage
from protoactor.router.router import Router

context = RootContext()
timeout = timedelta(milliseconds=1000)
my_actor_props = Props.from_producer(lambda: MyTestActor())


@pytest.mark.asyncio
async def test_consistent_hash_group_router_message_with_same_hash_always_goes_to_same_routee():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await context.send(router, Message('message1'))
    await context.send(router, Message('message1'))
    await context.send(router, Message('message1'))

    assert await context.request_future(routee1, 'received?', timeout) == 3
    assert await context.request_future(routee2, 'received?', timeout) == 0
    assert await context.request_future(routee3, 'received?', timeout) == 0


@pytest.mark.asyncio
async def test_consistent_hash_group_router_messages_with_different_hashes_go_to_different_routees():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await context.send(router, Message('message1'))
    await context.send(router, Message('message2'))
    await context.send(router, Message('message3'))

    assert await context.request_future(routee1, 'received?', timeout) == 1
    assert await context.request_future(routee2, 'received?', timeout) == 1
    assert await context.request_future(routee3, 'received?', timeout) == 1


@pytest.mark.asyncio
async def test_consistent_hash_group_router_message_with_same_hash_always_goes_to_same_routee_even_when_new_routee_added():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await context.send(router, Message('message1'))
    routee4 = context.spawn(my_actor_props)
    await context.send(router, AddRoutee(routee4))
    await context.send(router, Message('message1'))

    assert await context.request_future(routee1, 'received?', timeout) == 2
    assert await context.request_future(routee2, 'received?', timeout) == 0
    assert await context.request_future(routee3, 'received?', timeout) == 0


@pytest.mark.asyncio
async def test_consistent_hash_group_router_routees_can_be_removed():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await context.send(router, RemoveRoutee(routee1))
    routees = await context.request_future(router, GetRoutees(), timeout)

    assert routee1 not in routees.pids
    assert routee2 in routees.pids
    assert routee3 in routees.pids


@pytest.mark.asyncio
async def test_consistent_hash_group_router_routees_can_be_added():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()
    routee4 = context.spawn(my_actor_props)
    await context.send(router, AddRoutee(routee4))

    routees = await context.request_future(router, GetRoutees(), timeout)

    assert routee1 in routees.pids
    assert routee2 in routees.pids
    assert routee3 in routees.pids
    assert routee4 in routees.pids


@pytest.mark.asyncio
async def test_consistent_hash_group_router_removed_routees_no_longer_receive_messages():
    router, routee1, _, _ = create_broadcast_group_router_with3_routees()
    await context.send(router, RemoveRoutee(routee1))
    await context.send(router, Message('message1'))

    assert await context.request_future(routee1, 'received?', timeout) == 0


@pytest.mark.asyncio
async def test_consistent_hash_group_router_message_is_reassigned_when_routee_removed():
    router, routee1, routee2, _ = create_broadcast_group_router_with3_routees()

    await context.send(router, Message('message1'))
    assert await context.request_future(routee1, 'received?', timeout) == 1

    await context.send(router, RemoveRoutee(routee1))
    await context.send(router, Message('message1'))
    assert await context.request_future(routee2, 'received?', timeout) == 1


@pytest.mark.asyncio
async def test_consistent_hash_group_router_all_routees_receive_router_broadcast_messages():
    router, routee1, routee2, routee3 = create_broadcast_group_router_with3_routees()

    await context.send(router, BroadcastMessage(Message('hello')))

    assert await context.request_future(routee1, 'received?', timeout) == 1
    assert await context.request_future(routee2, 'received?', timeout) == 1
    assert await context.request_future(routee3, 'received?', timeout) == 1


def create_broadcast_group_router_with3_routees():
    routee1 = context.spawn_named(my_actor_props, str(uuid.uuid4()) + 'routee1')
    routee2 = context.spawn_named(my_actor_props, str(uuid.uuid4()) + 'routee2')
    routee3 = context.spawn_named(my_actor_props, str(uuid.uuid4()) + 'routee3')

    props = Router.new_consistent_hash_group([routee1, routee2, routee3], SuperIntelligentDeterministicHash.hash, 1 )
    router = context.spawn(props)
    return router, routee1, routee2, routee3


class Message(AbstractHashable):
    def __init__(self, value: str):
        self._value = value

    def hash_by(self) -> str:
        return self._value

    def __str__(self):
        return self._value


class SuperIntelligentDeterministicHash():
    @staticmethod
    def hash(hash_key: str) -> int:
        if hash_key.endswith('routee1'):
            return 10
        elif hash_key.endswith('routee2'):
            return 20
        elif hash_key.endswith('routee3'):
            return 30
        elif hash_key.endswith('routee4'):
            return 40
        elif hash_key.endswith('message1'):
            return 9
        elif hash_key.endswith('message2'):
            return 19
        elif hash_key.endswith('message3'):
            return 29
        elif hash_key.endswith('message4'):
            return 39
        else:
            return 0


class MyTestActor(Actor):
    def __init__(self):
        self._received_messages = []

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if msg == 'received?':
            await context.respond(len(self._received_messages))
        elif isinstance(msg, Message):
            self._received_messages.append(msg.__str__())
