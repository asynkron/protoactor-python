#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
import unittest
from datetime import timedelta, datetime
from unittest.mock import Mock
from protoactor.supervision import OneOfOneStrategy, SupervisorDirective, Supervisor
from protoactor.pid import PID
from protoactor.process_registry import ProcessRegistry
from protoactor.restart_statistics import RestartStatistics
from protoactor.process import LocalProcess
from protoactor.mailbox.mailbox import Mailbox
from protoactor.mailbox.messages import ResumeMailbox
from protoactor.messages import Restart, Stop
import queue

@pytest.fixture(scope='module', )
def supervisor_data():
    supervisor = Supervisor()
    mailbox = Mailbox(None, None, None, None)
    local_process = LocalProcess(mailbox)
    pid_child = PID(address='address', id='id', ref=local_process)
    restart_statistic = RestartStatistics(5, datetime(2017, 2, 15))

    return {
        'supervisor': supervisor,
        'mailbox': mailbox,
        'local_process': local_process,
        'pid_child': pid_child,
        'restart_statistic': restart_statistic
    }


def test_handle_failure_resume_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()

    exc = Exception()

    decider = lambda pid, cause : SupervisorDirective.Resume
    
    one_of_one = OneOfOneStrategy(decider, 10, timedelta(seconds = 20))
    one_of_one.handle_failure(supervisor_data['supervisor'], supervisor_data['pid_child'], supervisor_data['restart_statistic'], exc)

    supervisor_data['local_process'].send_system_message.assert_called_once_with(supervisor_data['pid_child'], ResumeMailbox())

def test_handle_failure_restart_directive_can_restart(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()

    supervisor_data['restart_statistic'].request_restart_permission = Mock()
    supervisor_data['restart_statistic'].request_restart_permission.return_value = True

    exc = Exception()

    decider = lambda pid, cause : SupervisorDirective.Restart
    
    one_of_one = OneOfOneStrategy(decider, 10, timedelta(seconds = 20))
    one_of_one.handle_failure(supervisor_data['supervisor'], supervisor_data['pid_child'], supervisor_data['restart_statistic'], exc)

    supervisor_data['local_process'].send_system_message.assert_called_once_with(supervisor_data['pid_child'], Restart())

def test_handle_failure_restart_directive_cant_restart(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()

    supervisor_data['restart_statistic'].request_restart_permission = Mock()
    supervisor_data['restart_statistic'].request_restart_permission.return_value = False

    exc = Exception()

    decider = lambda pid, cause : SupervisorDirective.Restart
    
    one_of_one = OneOfOneStrategy(decider, 10, timedelta(seconds = 20))
    one_of_one.handle_failure(supervisor_data['supervisor'], supervisor_data['pid_child'], supervisor_data['restart_statistic'], exc)

    supervisor_data['local_process'].send_system_message.assert_called_once_with(supervisor_data['pid_child'], Stop())


def test_handle_failure_stop_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()
    exc = Exception()

    decider = lambda pid, cause : SupervisorDirective.Stop
    
    one_of_one = OneOfOneStrategy(decider, 10, timedelta(seconds = 20))
    one_of_one.handle_failure(supervisor_data['supervisor'], supervisor_data['pid_child'], supervisor_data['restart_statistic'], exc)

    supervisor_data['local_process'].send_system_message.assert_called_once_with(supervisor_data['pid_child'], Stop())


def test_handle_failure_escalate_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()
    supervisor_data['supervisor'].escalate_failure = Mock()
    exc = Exception()

    decider = lambda pid, cause : SupervisorDirective.Escalate
    
    one_of_one = OneOfOneStrategy(decider, 10, timedelta(seconds = 20))
    one_of_one.handle_failure(supervisor_data['supervisor'], supervisor_data['pid_child'], supervisor_data['restart_statistic'], exc)

    supervisor_data['supervisor'].escalate_failure.assert_called_once_with(supervisor_data['pid_child'], exc)
