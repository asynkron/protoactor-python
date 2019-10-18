from unittest import mock

import pytest

from protoactor.actor.process import DeadLettersProcess, ProcessRegistry, ActorProcess
from protoactor.actor.utils import Singleton
from protoactor.actor.protos_pb2 import PID
from protoactor.mailbox.mailbox import DefaultMailbox


@pytest.fixture
def nohost():
    if ProcessRegistry in Singleton._instances:
        del Singleton._instances[ProcessRegistry]
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
    _pid, absent = ProcessRegistry().try_add('new_id', mock_process)
    assert _pid.address == ProcessRegistry().address
    assert _pid.id == 'new_id'


def test_remove(nohost: ProcessRegistry, mock_process):
    _pid, absent = ProcessRegistry().try_add('new_id', mock_process)
    assert ProcessRegistry().get(_pid) == mock_process
    ProcessRegistry().remove(_pid)
    assert isinstance(ProcessRegistry().get(_pid), DeadLettersProcess) is True


def test_get_deadletter():
    _pid = mock.Mock()
    _pid.address = 'other_host'
    _pid.pid = '9999'
    assert isinstance(ProcessRegistry().get(_pid), DeadLettersProcess) is True


def test_get_nonhost(nohost: ProcessRegistry, mock_process):
    _pid, absent = ProcessRegistry().try_add('new_id', mock_process)
    assert ProcessRegistry().get(_pid) == mock_process

# def test_get_sameaddress():
#     test_pid = PID(address='address', id='id')
#     lp  = ActorProcess(DefaultMailbox())
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
#     lp  = ActorProcess(DefaultMailbox())
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
#     lp = ActorProcess(DefaultMailbox())
#
#     pr = ProcessRegistry(lambda x: None)
#     pr.address = 'address'
#
#     new_lp = pr.get(test_pid)
#
#     assert isinstance(new_lp, DeadLettersProcess) is True
