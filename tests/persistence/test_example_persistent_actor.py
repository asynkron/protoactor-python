import sys
import threading
import uuid
from datetime import timedelta

import pytest

from protoactor.actor.actor_context import RootContext, Actor, AbstractContext
from protoactor.actor.messages import Started
from protoactor.actor.props import Props
from protoactor.persistence.persistence import Persistence
from tests.persistence.in_memory_provider import InMemoryProvider
from tests.test_fixtures.mock_mailbox import MockMailbox

root_context = RootContext()
initial_state = 1


@pytest.mark.asyncio
async def test_events_are_saved_to_persistence():
    def callback(o):
        assert isinstance(o, Multiplied)
        assert o.amount == 2

    _, pid, _, actor_id, provider_state = create_test_actor()
    await root_context.send(pid, Multiply(2))
    await provider_state.get_events(actor_id, 0, sys.maxsize, callback)


@pytest.mark.asyncio
async def test_snapshots_are_saved_to_persistence():
    threading_events, pid, _, actor_id, provider_state = create_test_actor()
    await root_context.send(pid, Multiply(10))
    await root_context.send(pid, RequestSnapshot())

    threading_events['process_multiply'].wait()
    snapshot, _ = await provider_state.get_snapshot(actor_id)

    assert isinstance(snapshot, State)
    assert snapshot.value == 10


@pytest.mark.asyncio
async def test_events_can_be_deleted():
    threading_events, pid, _, actor_id, provider_state = create_test_actor()
    await root_context.send(pid, Multiply(10))

    threading_events['process_multiply'].wait()
    await provider_state.delete_events(actor_id, 1)

    events = []
    await provider_state.get_events(actor_id, 0, sys.maxsize, lambda v: events.append(v))

    assert len(events) == 0


@pytest.mark.asyncio
async def test_snapshots_can_be_deleted():
    threading_events, pid, _, actor_id, provider_state = create_test_actor()
    await root_context.send(pid, Multiply(10))
    await root_context.send(pid, RequestSnapshot())

    threading_events['process_request_snapshot'].wait()
    await provider_state.delete_snapshots(actor_id, 1)

    snapshot, _ = await provider_state.get_snapshot(actor_id)
    assert snapshot is None


@pytest.mark.asyncio
async def test_given_events_only_state_is_restored_from_events():
    threading_events, pid, props, _, _ = create_test_actor()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    state = await restart_actor_and_get_state(pid, props)
    assert initial_state * 2 * 2 == state


@pytest.mark.asyncio
async def test_given_a_snapshot_only_state_is_restored_from_the_snapshot():
    threading_events, pid, props, actor_id, provider_state = create_test_actor()

    await provider_state.persist_snapshot(actor_id, 0, State(10))
    state = await restart_actor_and_get_state(pid, props)
    assert state == 10


@pytest.mark.asyncio
async def test_given_events_then_a_snapshot_state_should_be_restored_from_the_snapshot():
    threading_events, pid, props, _, _ = create_test_actor()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, RequestSnapshot())
    threading_events['process_request_snapshot'].wait()

    state = await restart_actor_and_get_state(pid, props)
    expected_state = initial_state * 2 * 2

    assert expected_state == state


@pytest.mark.asyncio
async def test_given_a_snapshot_and_subsequent_events_state_should_be_restored_from_snapshot_and_subsequent_events():
    threading_events, pid, props, _, _ = create_test_actor()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, RequestSnapshot())
    threading_events['process_request_snapshot'].wait()

    await root_context.send(pid, Multiply(4))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(8))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    state = await restart_actor_and_get_state(pid, props)
    expected_state = initial_state * 2 * 2 * 4 * 8

    assert expected_state == state


@pytest.mark.asyncio
async def test_given_multiple_snapshots_state_is_restored_from_most_recent_snapshot():
    threading_events, pid, props, actor_id, provider_state = create_test_actor()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, RequestSnapshot())
    threading_events['process_request_snapshot'].wait()
    threading_events['process_request_snapshot'].clear()

    await root_context.send(pid, Multiply(4))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, RequestSnapshot())
    threading_events['process_request_snapshot'].wait()
    threading_events['process_request_snapshot'].clear()

    await provider_state.delete_events(actor_id, 2)
    state = await restart_actor_and_get_state(pid, props)

    assert initial_state * 2 * 4 == state


@pytest.mark.asyncio
async def test_given_multiple_snapshots_delete_snapshot_obeys_index():
    threading_events, pid, props, actor_id, provider_state = create_test_actor()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, RequestSnapshot())
    threading_events['process_request_snapshot'].wait()
    threading_events['process_request_snapshot'].clear()

    await root_context.send(pid, Multiply(4))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, RequestSnapshot())
    threading_events['process_request_snapshot'].wait()
    threading_events['process_request_snapshot'].clear()

    await provider_state.delete_snapshots(actor_id, 0)
    await provider_state.delete_events(actor_id, 1)

    state = await restart_actor_and_get_state(pid, props)

    assert initial_state * 2 * 4 == state


@pytest.mark.asyncio
async def test_given_a_snapshot_and_events_when_snapshot_deleted_state_should_be_restored_from_events():
    threading_events, pid, props, actor_id, provider_state = create_test_actor()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, RequestSnapshot())
    threading_events['process_request_snapshot'].wait()
    threading_events['process_request_snapshot'].clear()

    await root_context.send(pid, Multiply(4))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(8))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await provider_state.delete_snapshots(actor_id, 3)

    state = await restart_actor_and_get_state(pid, props)

    assert initial_state * 2 * 2 * 4 * 8 == state


@pytest.mark.asyncio
async def test_index_increments_on_events_saved():
    threading_events, pid, _, _, _ = create_test_actor()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    index = await root_context.request_future(pid, GetIndex(), timedelta(seconds=1))
    assert index == 0

    await root_context.send(pid, Multiply(4))
    index = await root_context.request_future(pid, GetIndex(), timedelta(seconds=1))
    assert index == 1


@pytest.mark.asyncio
async def test_index_is_not_affected_by_taking_a_snapshot():
    threading_events, pid, _, _, _ = create_test_actor()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, RequestSnapshot())
    threading_events['process_request_snapshot'].wait()
    threading_events['process_request_snapshot'].clear()

    await root_context.send(pid, Multiply(4))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    index = await root_context.request_future(pid, GetIndex(), timedelta(seconds=1))
    assert index == 1


@pytest.mark.asyncio
async def test_index_is_correct_after_recovery():
    threading_events, pid, props, _, _ = create_test_actor()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(4))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await pid.stop()
    pid = root_context.spawn(props)
    state = await root_context.request_future(pid, GetState(), timedelta(seconds=1))
    index = await root_context.request_future(pid, GetIndex(), timedelta(seconds=1))

    assert index == 1
    assert state == initial_state * 2 * 4


@pytest.mark.asyncio
async def test_given_events_can_replay_from_start_index_to_end_index():
    threading_events, pid, _, actor_id, provider_state = create_test_actor()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(4))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(8))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    messages = []
    await provider_state.get_events(actor_id, 1, 2, lambda msg: messages.append(msg))

    assert len(messages) == 2
    assert messages[0].amount == 2
    assert messages[1].amount == 4


@pytest.mark.asyncio
async def test_can_use_separate_stores():
    threading_events = {'process_started': threading.Event(),
                        'process_get_state': threading.Event(),
                        'process_get_index': threading.Event(),
                        'process_request_snapshot': threading.Event(),
                        'process_multiply': threading.Event()}

    actor_id = str(uuid.uuid4())
    event_store = InMemoryProvider()
    snapshot_store = InMemoryProvider()
    props = Props.from_producer(lambda: ExamplePersistentActor(threading_events,
                                                               event_store,
                                                               snapshot_store,
                                                               actor_id)).with_mailbox(MockMailbox)
    pid = root_context.spawn(props)

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    event_store_messages = []
    await event_store.get_events(actor_id, 0, 1, lambda msg: event_store_messages.append(msg))
    assert len(event_store_messages) == 1

    snapshot_store_messages = []
    await snapshot_store.get_events(actor_id, 0, 1, lambda msg: snapshot_store_messages.append(msg))
    assert len(snapshot_store_messages) == 0


class RequestSnapshot():
    pass


class GetState():
    pass


class GetIndex():
    pass


class Multiply():
    def __init__(self, amount):
        self.amount = amount


class Multiplied():
    def __init__(self, amount):
        self.amount = amount


class State():
    def __init__(self, value):
        self.value = value


class ExamplePersistentActor(Actor):
    def __init__(self, events, event_store, snapshot_store, persistence_id):
        self._events = events
        self._state = State(1)
        self._persistence = Persistence.with_event_sourcing_and_snapshotting(event_store,
                                                                             snapshot_store,
                                                                             persistence_id,
                                                                             self.apply_event,
                                                                             self.apply_snapshot)

    def apply_event(self, event):
        if isinstance(event.data, Multiplied):
            self._state.value = self._state.value * event.data.amount

    def apply_snapshot(self, snapshot):
        if isinstance(snapshot.state, State):
            self._state = snapshot.state

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if isinstance(msg, Started):
            await self._persistence.recover_state()
            self._events['process_started'].set()
        elif isinstance(msg, GetState):
            await context.respond(self._state.value)
            self._events['process_get_state'].set()
        elif isinstance(msg, GetIndex):
            await context.respond(self._persistence.index)
            self._events['process_get_index'].set()
        elif isinstance(msg, RequestSnapshot):
            await self._persistence.persist_snapshot(State(self._state.value))
            self._events['process_request_snapshot'].set()
        elif isinstance(msg, Multiply):
            await self._persistence.persist_event(Multiplied(msg.amount))
            self._events['process_multiply'].set()


def create_test_actor():
    events = {'process_started': threading.Event(),
              'process_get_state': threading.Event(),
              'process_get_index': threading.Event(),
              'process_request_snapshot': threading.Event(),
              'process_multiply': threading.Event()}

    actor_id = str(uuid.uuid4())
    in_memory_provider = InMemoryProvider()
    props = Props.from_producer(lambda: ExamplePersistentActor(events,
                                                               in_memory_provider,
                                                               in_memory_provider,
                                                               actor_id)).with_mailbox(MockMailbox)
    pid = root_context.spawn(props)

    return events, pid, props, actor_id, in_memory_provider


async def restart_actor_and_get_state(pid, props):
    await pid.stop()
    pid = root_context.spawn(props)
    return await root_context.request_future(pid, GetState(), timedelta(seconds=1))
