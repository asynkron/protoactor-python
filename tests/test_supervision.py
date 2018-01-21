#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
from unittest.mock import Mock

import pytest

from protoactor.mailbox.mailbox import Mailbox
from protoactor.mailbox.messages import ResumeMailbox
from protoactor.messages import Restart, Stop
from protoactor.pid import PID
from protoactor.process import LocalProcess
from protoactor.restart_statistics import RestartStatistics
from protoactor.supervision import OneForOneStrategy, AllForOneStrategy, SupervisorDirective, Supervisor
from typing import List


class TestSupervisor(Supervisor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def escalate_failure(self, who, reason) -> None:
        print("escalate_failure")

    def restart_children(self, reason, *pids) -> None:
        print("restart_children")

    def stop_children(self, *pids) -> None:
        print("stop_children")

    def resume_children(self, *pids) -> None:
        print("resume_children")

    def children(self) -> List['PID']:
        return []


@pytest.fixture(scope='function', )
def supervisor_data():
    supervisor = TestSupervisor()
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


def test_oneforone_handle_failure_resume_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()
    supervisor_data['supervisor'].resume_children = Mock()
    exc = Exception()

    decider = lambda pid, cause: SupervisorDirective.Resume

    one_for_one = OneForOneStrategy(decider, 10, timedelta(seconds=20))
    one_for_one.handle_failure(supervisor_data['supervisor'],
                               supervisor_data['pid_child'],
                               supervisor_data['restart_statistic'],
                               exc)

    supervisor_data['supervisor'].resume_children\
        .assert_called_once_with(supervisor_data['pid_child'])


def test_oneforone_handle_failure_restart_directive_can_restart(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()
    supervisor_data['supervisor'].restart_children = Mock()
    exc = Exception()

    decider = lambda pid, cause: SupervisorDirective.Restart

    one_for_one = OneForOneStrategy(decider, 10, timedelta(seconds=20))
    one_for_one.handle_failure(supervisor_data['supervisor'],
                               supervisor_data['pid_child'],
                               supervisor_data['restart_statistic'],
                               exc)

    supervisor_data['supervisor'].restart_children\
        .assert_called_once_with(exc, supervisor_data['pid_child'])


def test_oneforone_handle_failure_restart_directive_cant_restart(supervisor_data):
    supervisor_data['supervisor'].stop_children = Mock()
    supervisor_data['restart_statistic'].number_of_failures = Mock(return_value=15)
    exc = Exception()

    decider = lambda pid, cause: SupervisorDirective.Restart

    one_for_one = OneForOneStrategy(decider, 10, timedelta(seconds=20))
    one_for_one.request_restart_permission = Mock(return_value=False)

    one_for_one.handle_failure(supervisor_data['supervisor'],
                               supervisor_data['pid_child'],
                               supervisor_data['restart_statistic'],
                               exc)

    supervisor_data['supervisor'].stop_children\
        .assert_called_once_with(supervisor_data['pid_child'])


def test_oneforone_handle_failure_stop_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()
    supervisor_data['supervisor'].stop_children = Mock()
    exc = Exception()

    decider = lambda pid, cause: SupervisorDirective.Stop

    one_for_one = OneForOneStrategy(decider, 10, timedelta(seconds=20))
    one_for_one.handle_failure(supervisor_data['supervisor'],
                               supervisor_data['pid_child'],
                               supervisor_data['restart_statistic'],
                               exc)

    supervisor_data['supervisor'].stop_children\
        .assert_called_once_with(supervisor_data['pid_child'])


def test_oneforone_handle_failure_escalate_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()
    supervisor_data['supervisor'].escalate_failure = Mock()
    exc = Exception()

    decider = lambda pid, cause: SupervisorDirective.Escalate

    one_for_one = OneForOneStrategy(decider, 10, timedelta(seconds=20))
    one_for_one.handle_failure(supervisor_data['supervisor'],
                               supervisor_data['pid_child'],
                               supervisor_data['restart_statistic'],
                               exc)

    supervisor_data['supervisor'].escalate_failure\
        .assert_called_once_with(supervisor_data['pid_child'], exc)


def test_allforone_handle_failure_resume_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()
    supervisor_data['supervisor'].resume_children = Mock()
    exc = Exception()

    decider = lambda pid, cause: SupervisorDirective.Resume

    one_for_one = AllForOneStrategy(decider, 10, timedelta(seconds=20))
    one_for_one.handle_failure(supervisor_data['supervisor'],
                               supervisor_data['pid_child'],
                               supervisor_data['restart_statistic'],
                               exc)

    supervisor_data['supervisor'].resume_children\
        .assert_called_once_with(supervisor_data['pid_child'])


def test_allforone_handle_failure_restart_directive_can_restart(supervisor_data):
    # TODO: delete ref after mergin migrating on the protobuf pids objects
    children_pids = [PID(address='address1', id='id1', ref=supervisor_data['local_process']),
                     PID(address='address2', id='id2', ref=supervisor_data['local_process'])]
    supervisor_data['local_process'].send_system_message = Mock()
    supervisor_data['supervisor'].restart_children = Mock()
    supervisor_data['supervisor'].children = Mock(return_value=children_pids)
    exc = Exception()

    decider = lambda pid, cause: SupervisorDirective.Restart

    one_for_one = AllForOneStrategy(decider, 10, timedelta(seconds=20))
    one_for_one.handle_failure(supervisor_data['supervisor'],
                               supervisor_data['pid_child'],
                               supervisor_data['restart_statistic'],
                               exc)

    supervisor_data['supervisor'].restart_children\
        .assert_called_once_with(exc, *children_pids)


def test_allforone_handle_failure_restart_directive_cant_restart(supervisor_data):
    # TODO: delete ref after mergin migrating on the protobuf pids objects
    children_pids = [PID(address='address1', id='id1', ref=supervisor_data['local_process']),
                     PID(address='address2', id='id2', ref=supervisor_data['local_process'])]
    supervisor_data['supervisor'].stop_children = Mock()
    supervisor_data['restart_statistic'].number_of_failures = Mock(return_value=15)
    supervisor_data['supervisor'].children = Mock(return_value=children_pids)
    exc = Exception()

    decider = lambda pid, cause: SupervisorDirective.Restart

    one_for_one = AllForOneStrategy(decider, 10, timedelta(seconds=20))
    one_for_one.request_restart_permission = Mock(return_value=False)

    one_for_one.handle_failure(supervisor_data['supervisor'],
                               supervisor_data['pid_child'],
                               supervisor_data['restart_statistic'],
                               exc)

    supervisor_data['supervisor'].stop_children\
        .assert_called_once_with(*children_pids)


def test_allforone_handle_failure_stop_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()
    supervisor_data['supervisor'].stop_children = Mock()
    exc = Exception()

    decider = lambda pid, cause: SupervisorDirective.Stop

    one_for_one = AllForOneStrategy(decider, 10, timedelta(seconds=20))
    one_for_one.handle_failure(supervisor_data['supervisor'],
                               supervisor_data['pid_child'],
                               supervisor_data['restart_statistic'],
                               exc)

    supervisor_data['supervisor'].stop_children\
        .assert_called_once_with(supervisor_data['pid_child'])


def test_allforone_handle_failure_escalate_directive(supervisor_data):
    supervisor_data['local_process'].send_system_message = Mock()
    supervisor_data['supervisor'].escalate_failure = Mock()
    exc = Exception()

    decider = lambda pid, cause: SupervisorDirective.Escalate

    one_for_one = AllForOneStrategy(decider, 10, timedelta(seconds=20))
    one_for_one.handle_failure(supervisor_data['supervisor'],
                               supervisor_data['pid_child'],
                               supervisor_data['restart_statistic'],
                               exc)

    supervisor_data['supervisor'].escalate_failure\
        .assert_called_once_with(supervisor_data['pid_child'], exc)
