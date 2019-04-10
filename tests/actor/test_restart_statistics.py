import datetime
from datetime import timedelta

from protoactor.actor.restart_statistics import RestartStatistics


def test_number_of_failures():
    rs = RestartStatistics(10, datetime.datetime(2017, 2, 14, 0, 0, 0))
    assert rs.number_of_failures(timedelta(days=1, seconds=1)) == 0


def test_number_of_failures_greater_then_zero():
    rs = RestartStatistics(10, datetime.datetime.now())
    assert rs.number_of_failures(timedelta(seconds=1)) == 10
