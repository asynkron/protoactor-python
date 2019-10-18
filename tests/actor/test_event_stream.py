import pytest

from protoactor.actor.event_stream import EventStream
from protoactor.mailbox.dispatcher import Dispatchers

@pytest.mark.asyncio
async def test_can_subscribe_to_specific_event_types():
    received_events = []

    async def fun(msg):
        received_events.append(msg)

    event_stream = EventStream()
    event_stream.subscribe(fun, str)
    await event_stream.publish('hello')

    assert received_events[0] == 'hello'

@pytest.mark.asyncio
async def test_can_subscribe_to_all_event_types():
    received_events = []

    async def fun(msg):
        received_events.append(msg)

    event_stream = EventStream()
    event_stream.subscribe(fun)

    await event_stream.publish('hello')
    assert received_events[0] == 'hello'

    await event_stream.publish(1)
    assert received_events[1] == 1

    await event_stream.publish(True)
    assert received_events[2] is True

@pytest.mark.asyncio
async def test_can_unsubscribe_from_events():
    received_events = []

    async def fun(msg):
        received_events.append(msg)

    event_stream = EventStream()
    subscription = event_stream.subscribe(fun, str)
    await event_stream.publish('first message')
    subscription.unsubscribe()
    await event_stream.publish('second message')

    assert len(received_events) == 1

@pytest.mark.asyncio
async def test_only_receive_subscribed_to_event_types():
    received_events = []

    async def fun(msg):
        received_events.append(msg)

    event_stream = EventStream()
    event_stream.subscribe(fun, int)
    await event_stream.publish('not an int')

    assert len(received_events) == 0

@pytest.mark.asyncio
async def test_can_subscribe_to_specific_event_types_async():

    async def fun(msg):
        received = msg
        assert received == 'hello'

    event_stream = EventStream()
    event_stream.subscribe(fun, str, Dispatchers().default_dispatcher)
    await event_stream.publish('hello')