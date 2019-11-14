import asyncio
import threading
import uuid
from datetime import timedelta

import pytest

from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import AbstractContext, RootContext
from protoactor.actor.props import Props
from protoactor.persistence.persistence import Persistence
from protoactor.persistence.snapshot_strategies.interval_strategy import IntervalStrategy
from protoactor.persistence.snapshot_strategies.time_strategy import TimeStrategy
from tests.persistence.in_memory_provider import InMemoryProvider
from tests.persistence.test_example_persistent_actor import Multiplied, Multiply, RequestSnapshot, State
from tests.test_fixtures.mock_mailbox import MockMailbox

root_context = RootContext()


@pytest.mark.asyncio
async def test_given_an_interval_strategy_should_save_snapshot_accordingly():
    threading_events, pid, _, actor_id, provider_state = create_test_actor(IntervalStrategy(1))

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    await root_context.send(pid, Multiply(2))
    threading_events['process_multiply'].wait()
    threading_events['process_multiply'].clear()

    snapshots = provider_state.get_snapshots(actor_id)
    assert len(snapshots) == 3
    assert snapshots[0] == 2
    assert snapshots[1] == 4
    assert snapshots[2] == 8

class ExamplePersistentActor(Actor):
    def __init__(self, events, event_store, snapshot_store, persistence_id, strategy):
        self._state = 1
        self._events = events
        self._persistence = Persistence.with_event_sourcing_and_snapshotting(event_store,
                                                                             snapshot_store,
                                                                             persistence_id,
                                                                             self.process_event,
                                                                             self.process_snapshot,
                                                                             strategy,
                                                                             lambda: self._state)

    def process_event(self, event):
        self._state = self._state * event.data.amount

    def process_snapshot(self, snapshot):
        self._state = snapshot.state

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if isinstance(msg, Multiply):
            await self._persistence.persist_event(Multiplied(msg.amount))
            self._events['process_multiply'].set()


def create_test_actor(strategy):
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
                                                               actor_id,
                                                               strategy)).with_mailbox(MockMailbox)
    pid = root_context.spawn(props)

    return events, pid, props, actor_id, in_memory_provider
