from protoactor.persistence.messages import PersistedEvent
from protoactor.persistence.snapshot_strategies.abstract_snapshot_strategy import AbstractSnapshotStrategy


class IntervalStrategy(AbstractSnapshotStrategy):
    def __init__(self, events_per_snapshot: int):
        self._events_per_snapshot = events_per_snapshot

    def should_take_snapshot(self, persisted_event: PersistedEvent) -> bool:
        return persisted_event.index % self._events_per_snapshot == 0