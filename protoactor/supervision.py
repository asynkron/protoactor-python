from abc import ABCMeta, abstractmethod
from typing import List
from enum import Enum

from . import pid
from .restart_statistics import RestartStatistics


class SupervisorDirective(Enum):
    Resume = 0
    Restart = 1
    Stop = 2
    Escalate = 3


class Supervisor(metaclass=ABCMeta):

    # TODO: use @abstractmethod
    def escalate_failure(self, who: 'PID', reason: Exception) -> None:
        raise NotImplementedError("Implement this on a subclass")

    # TODO: use @abstractmethod
    def restart_children(self, reason: Exception, *pids: List['PID']) -> None:
        raise NotImplementedError("Implement this on a subclass")

    # TODO: use @abstractmethod
    def stop_children(self, *pids: List['PID']) -> None:
        raise NotImplementedError("Implement this on a subclass")

    # TODO: use @abstractmethod
    def resume_children(self, *pids: List['PID']) -> None:
        raise NotImplementedError("Implement this on a subclass")

    def children(self) -> List['PID']:
        raise NotImplementedError("Implement this on a subclass")


class AbstractSupervisorStrategy(metaclass=ABCMeta):
    @abstractmethod
    def handle_failure(self, supervisor, child: pid.PID,
                       rs_stats: RestartStatistics,
                       reason: Exception):
        raise NotImplementedError("Should Implement this method")


class AllForOneStrategy(AbstractSupervisorStrategy):

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

        elif directive == SupervisorDirective.Restart:
            if self.should_stop(rs_stats):
                print("Stopping {0} reason: {1}".format(child, reason))
                supervisor.stop_children(*supervisor.children())
            else:
                print("Restarting {0} reason: {1}".format(child, reason))
                supervisor.restart_children(reason, *supervisor.children())

        elif directive == SupervisorDirective.Stop:
            print("Stopping {0} reason: {1}".format(child, reason))
            supervisor.stop_children(child)

        elif directive == SupervisorDirective.Escalate:
            supervisor.escalate_failure(child, reason)

        else:
            # TODO: raise not handle error
            pass

    def should_stop(self, rs_stats: RestartStatistics):
        if self.__max_retries_number == 0:
            return True

        rs_stats.fail()

        if rs_stats.number_of_failures(self.__within_timedelta) > self.__max_retries_number:
            rs_stats.reset()
            return True

        return False


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

        elif directive == SupervisorDirective.Restart:
            if self.should_stop(rs_stats):
                print("Restarting {0} reason: {1}".format(child, reason))
                supervisor.stop_children(child)
            else:
                print("Stopping  {0} reason: {1}".format(child, reason))
                supervisor.restart_children(reason, child)

        elif directive == SupervisorDirective.Stop:
            print("Stopping {0} reason: {1}".format(child, reason))
            supervisor.stop_children(child)

        elif directive == SupervisorDirective.Escalate:
            supervisor.escalate_failure(child, reason)

        else:
            # TODO: raise not handle error
            pass

    def should_stop(self, rs_stats: RestartStatistics):
        if self.__max_retries_number == 0:
            return True

        rs_stats.fail()

        if rs_stats.number_of_failures(self.__within_timedelta) > self.__max_retries_number:
            rs_stats.reset()
            return True

        return False


class AlwaysRestartStrategy(AbstractSupervisorStrategy):
    def handle_failure(self, supervisor, child: pid.PID,
                    rs_stats: RestartStatistics,
                    reason: Exception):

        supervisor.restart_children(reason, child)
