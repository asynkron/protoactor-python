import sys
from typing import Tuple, Callable, Any

from protoactor.persistence.messages import Event, Snapshot, RecoverSnapshot, RecoverEvent, PersistedEvent, \
    PersistedSnapshot
from protoactor.persistence.providers.abstract_provider import AbstractSnapshotStore, AbstractEventStore
from protoactor.persistence.snapshot_strategies.abstract_snapshot_strategy import AbstractSnapshotStrategy


class NoSnapshots(AbstractSnapshotStrategy):
    def should_take_snapshot(self, persisted_event) -> bool:
        return False


class NoEventStore(AbstractEventStore):
    async def get_events(self, actor_name: str, index_start: int, index_end: int,
                         callback: Callable[[any], None]) -> int:
        return sys.int_info.min

    async def persist_event(self, actor_name: str, index: int, event: any) -> int:
        pass

    async def delete_events(self, actor_name: str, inclusive_to_index: int) -> None:
        pass


class NoSnapshotStore(AbstractSnapshotStore):
    async def get_snapshot(self, actor_name: str) -> Tuple[any, int]:
        return None, 0

    async def persist_snapshot(self, actor_name: str, index: int, snapshot: any) -> None:
        pass

    async def delete_snapshots(self, actor_name: str, inclusive_to_index: int) -> None:
        pass


class Persistence():
    def __init__(self, event_store: AbstractEventStore,
                 snapshot_store: AbstractSnapshotStore,
                 actor_id: str,
                 apply_event: Callable[[Event], None] = None,
                 apply_snapshot: Callable[[Snapshot], None] = None,
                 snapshot_strategy: AbstractSnapshotStrategy = None,
                 get_state: Callable[[None], Any] = None):
        self._event_store = event_store
        self._snapshot_store = snapshot_store
        self._actor_id = actor_id
        self._apply_event = apply_event
        self._apply_snapshot = apply_snapshot
        self._get_state = get_state
        if snapshot_strategy is None:
            self._snapshot_strategy = NoSnapshots()
        else:
            self._snapshot_strategy = snapshot_strategy
        self._index = -1

    @property
    def index(self) -> int:
        return self._index

    @property
    def _using_snapshotting(self) -> bool:
        return self._apply_snapshot is not None

    @property
    def _using_event_sourcing(self) -> bool:
        return self._apply_event is not None

    @staticmethod
    def with_event_sourcing(event_store: AbstractEventStore,
                            actor_id: str,
                            apply_event: Callable[[Event], None]) -> 'Persistence':
        if event_store is None:
            raise ValueError('event store is empty')
        if apply_event is None:
            raise ValueError('apply event is empty')

        return Persistence(event_store, NoSnapshotStore(), actor_id, apply_event)

    @staticmethod
    def with_snapshotting(snapshot_store: AbstractSnapshotStore,
                          actor_id: str,
                          apply_snapshot: Callable[[Snapshot], None]) -> 'Persistence':
        if snapshot_store is None:
            raise ValueError('snapshot store is empty')
        if apply_snapshot is None:
            raise ValueError('apply snapshot is empty')

        return Persistence(NoEventStore(), snapshot_store, actor_id, None, apply_snapshot)

    @staticmethod
    def with_event_sourcing_and_snapshotting(event_store: AbstractEventStore,
                                             snapshot_store: AbstractSnapshotStore,
                                             actor_id: str,
                                             apply_event: Callable[[Event], None],
                                             apply_snapshot: Callable[[Snapshot], None],
                                             snapshot_strategy: AbstractSnapshotStrategy = None,
                                             get_state: Callable[[], Any] = None) -> 'Persistence':
        if event_store is None:
            raise ValueError('event store is empty')
        if snapshot_store is None:
            raise ValueError('snapshot store is empty')
        if apply_event is None:
            raise ValueError('apply event is empty')
        if apply_snapshot is None:
            raise ValueError('apply snapshot is empty')
        if snapshot_strategy is None and get_state is not None:
            raise ValueError('snapshot strategy is empty')
        if get_state is None and snapshot_strategy is not None:
            raise ValueError('get state is empty')

        return Persistence(event_store,
                           snapshot_store,
                           actor_id,
                           apply_event,
                           apply_snapshot,
                           snapshot_strategy,
                           get_state)

    async def recover_state(self) -> None:
        snapshot, last_snapshot_index = await self._snapshot_store.get_snapshot(self._actor_id)

        if snapshot is not None:
            self._index = last_snapshot_index
            self._apply_snapshot(RecoverSnapshot(snapshot, last_snapshot_index))

        def apply_events(event):
            self._index = self._index + 1
            self._apply_event(RecoverEvent(event, self._index))

        from_event_index = self._index + 1
        await self._event_store.get_events(self._actor_id, from_event_index, sys.maxsize, apply_events)

    async def replay_events(self, from_index: int, to_index: int) -> None:
        if self._apply_event is None:
            raise Exception('Events cannot be replayed without using Event Sourcing.')

        local_index = from_index

        def apply_events(event):
            self._apply_event(RecoverEvent(event, self.local_index))
            self.local_index = local_index + 1

        await self._event_store.get_events(self._actor_id, from_index, to_index, apply_events)

    async def persist_event(self, event: Any) -> None:
        if self._apply_event is None:
            raise Exception('Events cannot be replayed without using Event Sourcing.')

        persisted_event = PersistedEvent(event, self._index + 1)
        await self._event_store.persist_event(self._actor_id, persisted_event.index, persisted_event.data)

        self._index = self._index + 1
        self._apply_event(persisted_event)

        if self._snapshot_strategy.should_take_snapshot(persisted_event):
            persisted_snapshot = PersistedSnapshot(self._get_state(), persisted_event.index)
            await self._snapshot_store.persist_snapshot(self._actor_id,
                                                        persisted_snapshot.index,
                                                        persisted_snapshot.state)

    async def persist_snapshot(self, snapshot: Any) -> None:
        persisted_snapshot = PersistedSnapshot(snapshot, self._index)
        await self._snapshot_store.persist_snapshot(self._actor_id, persisted_snapshot.index, snapshot)

    async def delete_snapshots(self, inclusive_to_index: int) -> None:
        await self._snapshot_store.delete_snapshots(self._actor_id, inclusive_to_index)

    async def delete_events(self, inclusive_to_index: int) -> None:
        await self._event_store.delete_events(self._actor_id, inclusive_to_index)
