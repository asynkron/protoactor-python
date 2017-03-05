import pytest
from unittest import mock
from protoactor import pid


@pytest.fixture
def mocked_pid():
    _process = mock.Mock()
    _process.send_user_message = mock.MagicMock(return_value=None)
    _process.send_system_message = mock.MagicMock(return_value=None)
    _process.stop = mock.MagicMock(return_value=None)
    return pid.PID("sample_address", "sample_id", _process)


def test_adress(mocked_pid):
    assert mocked_pid.address == "sample_address"


def test_id(mocked_pid):
    assert mocked_pid.id == "sample_id"


def test_tell(mocked_pid):
    message = "test_message"
    mocked_pid.tell(message)
    mocked_pid.process.send_user_message.assert_called_once_with(mocked_pid, message)


def test_send_system_message(mocked_pid):
    message = "test_message"
    mocked_pid.send_system_message(message)
    mocked_pid.process.send_system_message.assert_called_once_with(mocked_pid, message)


def test_stop(mocked_pid):
    mocked_pid.stop()
    mocked_pid.process.stop.assert_called_once_with()
