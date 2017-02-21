import pytest
import datetime
import mock
from datetime import timedelta
from protoactor.restart_statistics import RestartStatistics

def test_request_restart_permission_max_retries_number_zero():
    rs = RestartStatistics(10, datetime.datetime.now())
    assert rs.request_restart_permission(0) == False

def test_request_restart_permission_within_timedelta_none():
    rs = RestartStatistics(10, datetime.datetime.now())
    r = rs.request_restart_permission(20)
    assert r == True

def test_request_restart_permission_within_timedelta_none():
    rs = RestartStatistics(10, datetime.datetime.now())
    r = rs.request_restart_permission(20)
    assert r == True

def test_request_restart_permission_failure_time_gt_then_now_time_minus_delta__failure_count_gt_max_retries_number():
    with mock.patch.object(datetime, 'datetime', mock.Mock(wraps=datetime.datetime)) as patched:
        patched.now.return_value = datetime.datetime(2017, 2, 15, 0, 0, 0)
        last_failure_date = datetime.datetime(2017, 2, 14, 0, 0, 0)

        rs = RestartStatistics(10, last_failure_date)
        r = rs.request_restart_permission(5, timedelta(days=1, seconds=1))
        assert r == False

def test_request_restart_permission_failure_time_gt_then_now_time_minus_delta__failure_count_lt_max_retries_number():
    with mock.patch.object(datetime, 'datetime', mock.Mock(wraps=datetime.datetime)) as patched:
        patched.now.return_value = datetime.datetime(2017, 2, 15, 0, 0, 0)
        last_failure_date = datetime.datetime(2017, 2, 14, 0, 0, 0)

        rs = RestartStatistics(10, last_failure_date)
        r = rs.request_restart_permission(15, timedelta(days=1, seconds=1))
        assert r == True
