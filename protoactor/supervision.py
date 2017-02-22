from abc import ABCMeta, abstractmethod

from .mailbox.messages import ResumeMailbox
from .messages import Restart, Stop
from .pid import PID
from .process import AbstractProcess
from .process_registry import ProcessRegistry
from .restart_statistics import RestartStatistics


class SupervisorDirective:
    Resume = 0
    Restart = 1
    Stop = 2
    Escalate = 3


class Supervisor:
    def escalate_failure(who, reason):
        raise NotImplementedError("Implement this on a subclass")


class AbstractSupervisorStrategy(metaclass=ABCMeta):
    @abstractmethod
    def handle_failure(self, supervisor, child: PID, rs_stats: RestartStatistics, reason: Exception, message: object):
        raise NotImplementedError("Should Implement this method")


class OneOfOneStrategy(AbstractSupervisorStrategy):
    def __init__(self, decider, max_retries_number, within_timedelta):
        self.__decider = decider
        self.__max_retries_number = max_retries_number
        self.__within_timedelta = within_timedelta

    def __get_pid_aref(self, pid: PID) -> AbstractProcess:
        return pid.process if pid.process is not None else ProcessRegistry().get(pid)

    def handle_failure(self, supervisor, child: PID, rs_stats: RestartStatistics, reason: Exception, message: object):
        directive = self.__decider(child, reason)

        if directive == SupervisorDirective.Resume:
            pid_aref = self.__get_pid_aref(child)
            pid_aref.send_system_message(child, ResumeMailbox())
            return

        if directive == SupervisorDirective.Restart:
            pid_aref = self.__get_pid_aref(child)
            if rs_stats.request_restart_permission(self.__max_retries_number, self.__within_timedelta):
                # TODO: Log console "Restarting {child.ToShortString()} Reason {exc_cause}"
                pid_aref.send_system_message(child, Restart())
            else:
                # TODO: Log console Stopping {child.ToShortString()} Reason { exc_cause}"
                pid_aref.send_system_message(child, Stop())
            return

        if directive == SupervisorDirective.Stop:
            # TODO: Log console Stopping {child.ToShortString()} Reason { exc_cause}"
            pid_aref = self.__get_pid_aref(child)
            pid_aref.send_system_message(child, Stop())
            return

        if directive == SupervisorDirective.Escalate:
            supervisor.escalate_failure(child, reason)
            return
