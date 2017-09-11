from abc import ABCMeta, abstractmethod
from typing import List

from . import pid
from .restart_statistics import RestartStatistics


class SupervisorDirective:
    Resume = 0
    Restart = 1
    Stop = 2
    Escalate = 3


class Supervisor(metaclass=ABCMeta):

    # TODO: use @abstractmethod
    def escalate_failure(self, who: 'PID', reason: Exception) -> None:
        raise NotImplementedError("Implement this on a subclass")

    # TODO: use @abstractmethod
    def restart_children(self, *pids: List['PID']) -> None:
        raise NotImplementedError("Implement this on a subclass")

    # TODO: use @abstractmethod
    def stop_children(self, *pids: List['PID']) -> None:
        raise NotImplementedError("Implement this on a subclass")

    # TODO: use @abstractmethod
    def resume_children(self, *pids: List['PID']) -> None:
        raise NotImplementedError("Implement this on a subclass")


class AbstractSupervisorStrategy(metaclass=ABCMeta):
    @abstractmethod
    def handle_failure(self, supervisor, child: pid.PID,
                       rs_stats: RestartStatistics,
                       reason: Exception):
        raise NotImplementedError("Should Implement this method")


class OneForOneStrategy(AbstractSupervisorStrategy):

    def __init__(self, decider, max_retries_number, within_timedelta):
        self.__decider = decider
        self.__max_retries_number = max_retries_number
        self.__within_timedelta = within_timedelta

    def handle_failure(self, supervisor, child: pid.PID,
                       rs_stats: RestartStatistics,
                       reason: Exception):
        directive = self.__decider(child, reason)

        if directive == SupervisorDirective.Resume:
            supervisor.resume_children(child)
            return

        if directive == SupervisorDirective.Restart:
            if self.request_restart_permission(rs_stats):
                print("Restarting {0} reason: {1}".format(child, reason))
                supervisor.restart_children(child)
            else:
                print("Restarting {0} reason: {1}".format(child, reason))
                supervisor.stop_children(child)
            return

        if directive == SupervisorDirective.Stop:
            print("Stopping {0} reason: {1}".format(child, reason))
            supervisor.stop_children(child)
            return

        if directive == SupervisorDirective.Escalate:
            supervisor.escalate_failure(child, reason)
            return

    def request_restart_permission(self, rs: RestartStatistics) -> bool:
        if self.__max_retries_number == 0:
            return False
        rs.fail()

        if self.__within_timedelta is None or rs.is_within_duration(self.__within_timedelta):
            return self.__failure_count <= self.__max_retries_number

        rs.reset()
        return True
