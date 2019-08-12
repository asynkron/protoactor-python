import pytest

from protoactor.persistence.messages import PersistedEvent
from protoactor.persistence.snapshot_strategies.interval_strategy import IntervalStrategy


@pytest.mark.parametrize("interval,expected",
                         [(1, [1, 2, 3, 4, 5]),
                          (2, [2, 4, 6, 8, 10]),
                          (5, [5, 10, 15, 20, 25])])
def test_interval_strategy_should_snapshot_according_to_the_interval(interval, expected):
    strategy = IntervalStrategy(interval)
    for index in range(1, expected[-1]):
        if index in expected:
            assert strategy.should_take_snapshot(PersistedEvent(None, index)) == True
        else:
            assert strategy.should_take_snapshot(PersistedEvent(None, index)) == False
