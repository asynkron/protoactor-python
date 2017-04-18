import pytest
from unittest import mock
from protoactor import protos_pb2


@pytest.fixture
def mocked_pid():
    _process = mock.Mock()
    _process.send_user_message = mock.MagicMock(return_value=None)
    _process.send_system_message = mock.MagicMock(return_value=None)
    _process.stop = mock.MagicMock(return_value=None)
    pid = mock.Mock()
    pid.address = "sample_address"
    pid.id = "sample_id"
    pid.process = _process
    return pid


def test_address(mocked_pid):
    assert mocked_pid.address == "sample_address"


def test_id(mocked_pid):
    assert mocked_pid.Id == "sample_id"


def test_process(mocked_pid):
    _process = mock.Mock()
    mocked_pid.process = _process
    assert mocked_pid.process == _process


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


def test_repr(mocked_pid):
    return str(mocked_pid) == "{} / {}".format(mocked_pid.address, mocked_pid.id)
