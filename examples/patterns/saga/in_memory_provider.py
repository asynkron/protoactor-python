from typing import Tuple, Callable

from protoactor.persistence.messages import Snapshot
from protoactor.persistence.providers.abstract_provider import AbstractProvider


class InMemoryProvider(AbstractProvider):
    def __init__(self):
        self._events = {}

    async def get_snapshot(self, actor_name: str) -> Tuple[any, int]:
        return Snapshot, 0

    async def get_events(self, actor_name: str, index_start: int, index_end: int,
                         callback: Callable[[any], None]) -> int:
        if events := self._events.get(actor_name):
            for e in events:
                if index_start <= e.key <= index_end:
                    callback(e.value)
        return 0

    async def persist_event(self, actor_name: str, index: int, event: any) -> int:
        events = self._events.setdefault(actor_name, {})
        next_event_index = 1
        if len(events) != 0:
            next_event_index = list(events.items())[-1][0] + 1
        events[next_event_index] = event
        return 0

    async def persist_snapshot(self, actor_name: str, index: int, snapshot: any) -> None:
        pass

    async def delete_events(self, actor_name: str, inclusive_to_index: int) -> None:
        events = self._events.get(actor_name)
        if events is None:
            pass
        events_to_remove = list(filter(lambda s: s.key <= inclusive_to_index, events.items()))
        for event in events_to_remove:
            del self._events[event.key]

    async def delete_snapshots(self, actor_name: str, inclusive_to_index: int) -> None:
        pass
