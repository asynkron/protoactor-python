#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
from unittest import mock

import pytest

from protoactor.mailbox.mailbox import Mailbox
from protoactor.mailbox.messages import ResumeMailbox
from protoactor.messages import Restart, Stop
from protoactor import protos_pb2
from protoactor.process import LocalProcess
from protoactor.restart_statistics import RestartStatistics
from protoactor.supervision import OneForOneStrategy, SupervisorDirective, Supervisor


@pytest.fixture(scope='module', )
def supervisor_data():
    supervisor = Supervisor()
    mailbox = Mailbox(None, None, None, None)
    local_process = LocalProcess(mailbox)
    pid_child = mock.Mock()
    pid_child.address = 'address'
    pid_child.id = 'id'
    pid_child.process = local_process
    restart_statistic = RestartStatistics(5, datetime(2017, 2, 15))

    return {
        'supervisor': supervisor,
        'mailbox': mailbox,
        'local_process': local_process,
        'pid_child': pid_child,
        'restart_statistic': restart_statistic
    }


def test_handle_failure_resume_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = mock.Mock()

    exc = Exception()

    decider = lambda pid, cause : SupervisorDirective.Resume

    one_for_one = OneForOneStrategy(decider, 10, timedelta(seconds = 20))
    one_for_one.handle_failure(supervisor_data['supervisor'], supervisor_data['pid_child'], supervisor_data['restart_statistic'], exc)


    assert supervisor_data['local_process'].send_system_message.call_count == 1
    (called_pid, called_message), _ = supervisor_data['local_process'].send_system_message.call_args
    assert called_pid == supervisor_data['pid_child']
    assert isinstance(called_message, ResumeMailbox) is True


def test_handle_failure_restart_directive_can_restart(supervisor_data):
    supervisor_data['local_process'].send_system_message = mock.Mock()

    supervisor_data['restart_statistic'].request_restart_permission = mock.Mock()
    supervisor_data['restart_statistic'].request_restart_permission.return_value = True

    exc = Exception()

    decider = lambda pid, cause : SupervisorDirective.Restart

    one_for_one = OneForOneStrategy(decider, 10, timedelta(seconds = 20))
    one_for_one.handle_failure(supervisor_data['supervisor'], supervisor_data['pid_child'], supervisor_data['restart_statistic'], exc)

    assert supervisor_data['local_process'].send_system_message.call_count == 1
    (called_pid, called_message), _ = supervisor_data['local_process'].send_system_message.call_args
    assert called_pid == supervisor_data['pid_child']
    assert isinstance(called_message, Restart) is True


def test_handle_failure_restart_directive_cant_restart(supervisor_data):
    supervisor_data['local_process'].send_system_message = mock.Mock()

    supervisor_data['restart_statistic'].request_restart_permission = mock.Mock()
    supervisor_data['restart_statistic'].request_restart_permission.return_value = False

    exc = Exception()

    decider = lambda pid, cause : SupervisorDirective.Restart

    one_for_one = OneForOneStrategy(decider, 10, timedelta(seconds = 20))
    one_for_one.handle_failure(supervisor_data['supervisor'], supervisor_data['pid_child'], supervisor_data['restart_statistic'], exc)

    assert supervisor_data['local_process'].send_system_message.call_count == 1
    (called_pid, called_message), _ = supervisor_data['local_process'].send_system_message.call_args
    assert called_pid == supervisor_data['pid_child']
    assert isinstance(called_message, Stop) is True


def test_handle_failure_stop_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = mock.Mock()
    exc = Exception()

    decider = lambda pid, cause : SupervisorDirective.Stop

    one_for_one = OneForOneStrategy(decider, 10, timedelta(seconds = 20))
    one_for_one.handle_failure(supervisor_data['supervisor'], supervisor_data['pid_child'], supervisor_data['restart_statistic'], exc)

    assert supervisor_data['local_process'].send_system_message.call_count == 1
    (called_pid, called_message), _ = supervisor_data['local_process'].send_system_message.call_args
    assert called_pid == supervisor_data['pid_child']
    assert isinstance(called_message, Stop) is True


def test_handle_failure_escalate_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = mock.Mock()
    supervisor_data['supervisor'].escalate_failure = mock.Mock()
    exc = Exception()

    decider = lambda pid, cause : SupervisorDirective.Escalate

    one_for_one = OneForOneStrategy(decider, 10, timedelta(seconds = 20))
    one_for_one.handle_failure(supervisor_data['supervisor'], supervisor_data['pid_child'], supervisor_data['restart_statistic'], exc)

    supervisor_data['supervisor'].escalate_failure.assert_called_once_with(supervisor_data['pid_child'], exc)
