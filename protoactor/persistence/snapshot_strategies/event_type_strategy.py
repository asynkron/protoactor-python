from protoactor.persistence.messages import PersistedEvent
from protoactor.persistence.snapshot_strategies.abstract_snapshot_strategy import AbstractSnapshotStrategy


class EventTypeStrategy(AbstractSnapshotStrategy):
    def __init__(self, event_type):
        self._event_type = event_type

    def should_take_snapshot(self, persisted_event: PersistedEvent) -> bool:
        return self._event_type == type(persisted_event.data)
