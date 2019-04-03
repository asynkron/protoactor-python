from protoactor.actor.event_stream import EventStream
from protoactor.mailbox.dispatcher import Dispatchers


def test_can_subscribe_to_specific_event_types():
    received_events = []

    async def fun(msg):
        received_events.append(msg)

    event_stream = EventStream()
    event_stream.subscribe(fun, str)
    event_stream.publish('hello')

    assert received_events[0] == 'hello'


def test_can_subscribe_to_all_event_types():
    received_events = []

    async def fun(msg):
        received_events.append(msg)

    event_stream = EventStream()
    event_stream.subscribe(fun)

    event_stream.publish('hello')
    assert received_events[0] == 'hello'

    event_stream.publish(1)
    assert received_events[1] == 1

    event_stream.publish(True)
    assert received_events[2] is True


def test_can_unsubscribe_from_events():
    received_events = []

    async def fun(msg):
        received_events.append(msg)

    event_stream = EventStream()
    subscription = event_stream.subscribe(fun, str)
    event_stream.publish('first message')
    subscription.unsubscribe()
    event_stream.publish('second message')

    assert len(received_events) == 1


def test_only_receive_subscribed_to_event_types():
    received_events = []

    async def fun(msg):
        received_events.append(msg)

    event_stream = EventStream()
    event_stream.subscribe(fun, int)
    event_stream.publish('not an int')

    assert len(received_events) == 0


def test_can_subscribe_to_specific_event_types_async():

    async def fun(msg):
        received = msg
        assert received == 'hello'

    event_stream = EventStream()
    event_stream.subscribe(fun, str, Dispatchers().default_dispatcher)
    event_stream.publish('hello')