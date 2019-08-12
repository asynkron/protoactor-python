import datetime
from datetime import timedelta
from typing import Callable

from protoactor.persistence.messages import PersistedEvent
from protoactor.persistence.snapshot_strategies.abstract_snapshot_strategy import AbstractSnapshotStrategy


class TimeStrategy(AbstractSnapshotStrategy):
    def __init__(self, interval: timedelta, get_now: Callable[[], datetime.datetime] = None):
        self._interval = interval
        if get_now is None:
            self._get_now = lambda: datetime.datetime.now()
        else:
            self._get_now = get_now
        self._last_taken = self._get_now()

    def should_take_snapshot(self, persisted_event: PersistedEvent) -> bool:
        now = self._get_now()
        if (self._last_taken + self._interval) <= now:
            self._last_taken = now
            return True

        return False
