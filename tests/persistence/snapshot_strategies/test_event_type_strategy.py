from protoactor.persistence.messages import PersistedEvent
from protoactor.persistence.snapshot_strategies.event_type_strategy import EventTypeStrategy


def test_event_type_strategy_should_snapshot_according_to_the_event_type():
    strategy = EventTypeStrategy(type(int()))
    assert strategy.should_take_snapshot(PersistedEvent(1, 0)) == True
    assert strategy.should_take_snapshot(PersistedEvent("not an int", 0)) == False