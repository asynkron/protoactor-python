import pytest
import datetime
from datetime import timedelta
from protoactor.restart_statistics import RestartStatistics


def test_is_within_duration():
    rs = RestartStatistics(10, datetime.datetime(2017, 2, 14, 0, 0, 0))
    assert rs.is_within_duration(timedelta(days=1, seconds=1)) is False


def test_is_not_within_duration():
    rs = RestartStatistics(10, datetime.datetime.now())
    assert rs.is_within_duration(timedelta(seconds=1)) is True
