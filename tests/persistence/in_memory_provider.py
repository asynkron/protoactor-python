import copy
import json
from collections import OrderedDict
from typing import Tuple, Callable, Dict

from protoactor.persistence.providers.abstract_provider import AbstractProvider


class InMemoryProvider(AbstractProvider):
    def __init__(self):
        self._events = {}
        self._snapshots = {}

    def get_snapshots(self, actor_id: str) -> Dict[str, str]:
        return self._snapshots[actor_id]

    async def get_snapshot(self, actor_name: str) -> Tuple[any, int]:
        if actor_name not in self._snapshots.keys():
            self._snapshots[actor_name] = {}
            return None, 0

        ordered_snapshots = OrderedDict(self._snapshots[actor_name])
        if len(ordered_snapshots) == 0:
            return None, 0
        else:
            snapshot = list(ordered_snapshots.items())[-1]
            return snapshot[1], snapshot[0]

    async def get_events(self, actor_name: str, index_start: int, index_end: int,
                         callback: Callable[[any], None]) -> int:
        if actor_name in self._events.keys():
            for value in [value for key, value in self._events[actor_name].items() if index_start <= key <= index_end]:
                callback(value)
        else:
            return 0

    async def persist_event(self, actor_name: str, index: int, event: any) -> int:
        events = self._events.setdefault(actor_name, {})
        events[index] = event
        return 0

    async def persist_snapshot(self, actor_name: str, index: int, snapshot: any) -> None:
        snapshots = self._snapshots.setdefault(actor_name, {})
        snapshot_copy = copy.deepcopy(snapshot)
        snapshots[index] = snapshot_copy

    async def delete_events(self, actor_name: str, inclusive_to_index: int) -> None:
        if actor_name in self._events.keys():
            events_to_remove = [key for key, value in self._events[actor_name].items() if key <= inclusive_to_index]
            for key in events_to_remove:
                del self._events[actor_name][key]

    async def delete_snapshots(self, actor_name: str, inclusive_to_index: int) -> None:
        if actor_name in self._snapshots.keys():
            snapshots_to_remove = [key for key, value in self._snapshots[actor_name].items() if
                                   key <= inclusive_to_index]
            for key in snapshots_to_remove:
                del self._snapshots[actor_name][key]
