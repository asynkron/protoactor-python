import datetime

from protoactor.persistence.messages import PersistedEvent
from protoactor.persistence.snapshot_strategies.time_strategy import TimeStrategy


def test_time_strategy_should_snapshot_according_to_the_interval():
    now = datetime.datetime.strptime('2000-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')
    strategy = TimeStrategy(datetime.timedelta(seconds=10), lambda: now)
    assert strategy.should_take_snapshot(PersistedEvent(None, 0)) is False
    now = now + datetime.timedelta(seconds=5)
    assert strategy.should_take_snapshot(PersistedEvent(None, 0)) is False
    now = now + datetime.timedelta(seconds=5)
    assert strategy.should_take_snapshot(PersistedEvent(None, 0)) is True
    now = now + datetime.timedelta(seconds=5)
    assert strategy.should_take_snapshot(PersistedEvent(None, 0)) is False
    now = now + datetime.timedelta(seconds=5)
    assert strategy.should_take_snapshot(PersistedEvent(None, 0)) is True