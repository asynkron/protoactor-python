import pytest
from unittest import mock
from protoactor.process_registry import ProcessRegistry
from protoactor.process import LocalProcess
from protoactor.mailbox.mailbox import Mailbox
from protoactor.process import DeadLettersProcess


@pytest.fixture
def nohost():
    return ProcessRegistry()


@pytest.fixture
def mock_process():
    return mock.Mock()


def test_nonhost_address(nohost: ProcessRegistry):
    assert nohost.address == 'nonhost'


def test_set_address(nohost: ProcessRegistry):
    nohost.address = 'new_host'
    assert nohost.address == 'new_host'


def test_next_id(nohost: ProcessRegistry):
    assert nohost.next_id() == '1'


def test_add(nohost: ProcessRegistry, mock_process):
    _pid = ProcessRegistry().add('new_id', mock_process)
    assert _pid.address == ProcessRegistry().address
    assert _pid.id == 'new_id'
    #assert _pid.process == mock_process


def test_remove(nohost: ProcessRegistry, mock_process):
    _pid = ProcessRegistry().add('new_id', mock_process)
    assert ProcessRegistry().get(_pid) == mock_process
    ProcessRegistry().remove(_pid)
    assert isinstance(ProcessRegistry().get(_pid), DeadLettersProcess) is True


def test_get_deadletter():
    _pid = mock.Mock()
    _pid.address = 'other_host'
    _pid.pid = '9999'
    assert isinstance(ProcessRegistry().get(_pid), DeadLettersProcess) is True


def test_get_nonhost(nohost: ProcessRegistry, mock_process):
    _pid = ProcessRegistry().add('new_id', mock_process)
    assert ProcessRegistry().get(_pid) == mock_process

# def test_get_sameaddress():
#     test_pid = PID(address='address', id='id')
#     lp  = LocalProcess(Mailbox())
#
#     pr = ProcessRegistry(lambda x: lp if x == test_pid else None)
#     pr.address = 'address'
#
#     new_lp = pr.get(test_pid)
#
#     assert isinstance(new_lp, DeadLettersProcess) is True
#
#
# def test_get_not_sameaddress():
#     test_pid = PID(address='another_address', id='id')
#     lp  = LocalProcess(Mailbox())
#
#     pr = ProcessRegistry(lambda x: lp if x == test_pid else None)
#     pr.address = 'address'
#
#     new_lp = pr.get(test_pid)
#
#     assert test_pid.aref == lp
#
# def test_get__local_actor_refs_not_has_id_DeadLettersProcess():
#     test_pid = PID(address='address', id='id')
#     lp = LocalProcess(Mailbox())
#
#     pr = ProcessRegistry(lambda x: None)
#     pr.address = 'address'
#
#     new_lp = pr.get(test_pid)
#
#     assert isinstance(new_lp, DeadLettersProcess) is True
