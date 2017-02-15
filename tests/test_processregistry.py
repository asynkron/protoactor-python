import pytest
from master_protoactor.processregistry import ProcessRegistry
from master_protoactor.pid import PID
from master_protoactor.process import LocalProcess
from master_protoactor.mailbox import MailBox
from master_protoactor.process import DeadLettersProcess

def test_get_nohost():
    test_pid = PID(address='nohost', id='id')
    lp  = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: lp if x == test_pid else None)
    new_lp = pr.get(test_pid)

    assert test_pid.ref == lp


def test_get_sameaddress():
    test_pid = PID(address='address', id='id')
    lp  = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: lp if x == test_pid else None)
    pr.address = 'address'

    new_lp = pr.get(test_pid)

    assert test_pid.ref == lp


def test_get__local_actor_refs_not_has_id_DeadLettersProcess():
    test_pid = PID(address='another_address', id='id')
    lp = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: None)
    pr.address = 'address'

    new_lp = pr.get(test_pid)

    assert (type (new_lp) is DeadLettersProcess) == True

def test_add():
    test_pid = PID(address='another_address', id='id')
    lp = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: None)
    pr.address = 'address'

    pr.add('id', lp)
    new_lp = pr.get(test_pid)

    assert (type (new_lp) is DeadLettersProcess) == False


def test_remove():
    test_pid = PID(address='another_address', id='id')
    lp = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: None)
    pr.address = 'address'

    pr.add('id', lp)
    added_lp = pr.get(test_pid)
    assert (type (added_lp) is DeadLettersProcess) == False

    pr.remove(test_pid)
    removed_lp = pr.get(test_pid)
    assert (type (removed_lp) is DeadLettersProcess) == True

def test_next_id():
    test_pid = PID(address='another_address', id='id')
    lp = LocalProcess(MailBox())
    
    pr = ProcessRegistry(lambda x: None)
    pr.address = 'address'

    assert pr.next_id() == 1
