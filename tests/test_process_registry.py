import pytest
from protoactor.process_registry import ProcessRegistry
from protoactor.pid import PID
from protoactor.process import LocalProcess
from protoactor.mailbox import MailBox
from protoactor.process import DeadLettersProcess

def test_get_nohost():
    test_pid = PID(address='nonhost', id='id')
    lp  = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: lp if x == test_pid else None)
    new_lp = pr.get(test_pid)

    assert isinstance(new_lp, DeadLettersProcess) is True


def test_get_sameaddress():
    test_pid = PID(address='address', id='id')
    lp  = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: lp if x == test_pid else None)
    pr.address = 'address'

    new_lp = pr.get(test_pid)

    assert isinstance(new_lp, DeadLettersProcess) is True


def test_get_not_sameaddress():
    test_pid = PID(address='another_address', id='id')
    lp  = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: lp if x == test_pid else None)
    pr.address = 'address'

    new_lp = pr.get(test_pid)

    assert test_pid.aref == lp

def test_get__local_actor_refs_not_has_id_DeadLettersProcess():
    test_pid = PID(address='address', id='id')
    lp = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: None)
    pr.address = 'address'

    new_lp = pr.get(test_pid)

    assert isinstance(new_lp, DeadLettersProcess) is True

def test_add():
    test_pid = PID(address='address', id='id')
    lp = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: None)
    pr.address = 'address'

    pr.add('id', lp)
    new_lp = pr.get(test_pid)

    assert isinstance(new_lp, DeadLettersProcess) is False


def test_remove():
    test_pid = PID(address='address', id='id')
    lp = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: None)
    pr.address = 'address'

    pr.add('id', lp)
    added_lp = pr.get(test_pid)
    assert isinstance(added_lp, DeadLettersProcess) is False

    pr.remove(test_pid)
    removed_lp = pr.get(test_pid)
    assert isinstance(removed_lp, DeadLettersProcess) is True

def test_next_id():
    test_pid = PID(address='another_address', id='id')
    lp = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: None)
    pr.address = 'address'

    assert pr.next_id() == 1
