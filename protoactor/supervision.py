from abc import ABCMeta, abstractmethod

from . import messages, pid, process, process_registry, restart_statistics
from .mailbox.messages import ResumeMailbox


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
    def handle_failure(self, supervisor, child: pid.PID, rs_stats: restart_statistics.RestartStatistics,
                       reason: Exception, message: object):
        raise NotImplementedError("Should Implement this method")


class OneOfOneStrategy(AbstractSupervisorStrategy):
    def __init__(self, decider, max_retries_number, within_timedelta):
        self.__decider = decider
        self.__max_retries_number = max_retries_number
        self.__within_timedelta = within_timedelta

    def __get_pid_aref(self, pid: pid.PID) -> process.AbstractProcess:
        return pid.process if pid.process is not None else process_registry.ProcessRegistry().get(pid)

    def handle_failure(self, supervisor, child: pid.PID, rs_stats: restart_statistics.RestartStatistics,
                       reason: Exception, message: object):
        directive = self.__decider(child, reason)

        if directive == SupervisorDirective.Resume:
            pid_aref = self.__get_pid_aref(child)
            pid_aref.send_system_message(child, ResumeMailbox())
            return

        if directive == SupervisorDirective.Restart:
            pid_aref = self.__get_pid_aref(child)
            if rs_stats.request_restart_permission(self.__max_retries_number, self.__within_timedelta):
                # TODO: Log console "Restarting {child.ToShortString()} Reason {exc_cause}"
                pid_aref.send_system_message(child, messages.Restart())
            else:
                # TODO: Log console Stopping {child.ToShortString()} Reason { exc_cause}"
                pid_aref.send_system_message(child, messages.Stop())
            return

        if directive == SupervisorDirective.Stop:
            # TODO: Log console Stopping {child.ToShortString()} Reason { exc_cause}"
            pid_aref = self.__get_pid_aref(child)
            pid_aref.send_system_message(child, messages.Stop())
            return

        if directive == SupervisorDirective.Escalate:
            supervisor.escalate_failure(child, reason)
            return
