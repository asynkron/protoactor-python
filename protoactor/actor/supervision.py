from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import List

from protoactor.actor.protos_pb2 import PID
from .log import get_logger
from .restart_statistics import RestartStatistics


class SupervisorDirective(Enum):
    Resume = 0
    Restart = 1
    Stop = 2
    Escalate = 3


class AbstractSupervisor(metaclass=ABCMeta):

    @abstractmethod
    async def escalate_failure(self, who: 'PID', reason: Exception) -> None:
        raise NotImplementedError("Implement this on a subclass")

    @abstractmethod
    async def restart_children(self, reason: Exception, *pids: List['PID']) -> None:
        raise NotImplementedError("Implement this on a subclass")

    @abstractmethod
    async def stop_children(self, *pids: List['PID']) -> None:
        raise NotImplementedError("Implement this on a subclass")

    @abstractmethod
    async def resume_children(self, *pids: List['PID']) -> None:
        raise NotImplementedError("Implement this on a subclass")

    @abstractmethod
    def children(self) -> List['PID']:
        raise NotImplementedError("Implement this on a subclass")


class AbstractSupervisorStrategy(metaclass=ABCMeta):
    @abstractmethod
    async def handle_failure(self, supervisor, child: PID, rs_stats: RestartStatistics, reason: Exception):
        raise NotImplementedError("Should Implement this method")


class AllForOneStrategy(AbstractSupervisorStrategy):

    def __init__(self, decider, max_retries_number, within_timedelta):
        self._decider = decider
        self._max_retries_number = max_retries_number
        self._within_timedelta = within_timedelta
        self._logger = get_logger('OneForOneStrategy')

    async def handle_failure(self, supervisor, child: PID,
                       rs_stats: RestartStatistics,
                       reason: Exception):
        directive = self._decider(child, reason)

        if directive == SupervisorDirective.Resume:
            await supervisor.resume_children(child)

        elif directive == SupervisorDirective.Restart:
            if self.should_stop(rs_stats):
                print(f'Stopping {child} reason: {reason}')
                await supervisor.stop_children(*supervisor.children())
            else:
                print(f'Restarting {child} reason: {reason}')
                await supervisor.restart_children(reason, supervisor.children())

        elif directive == SupervisorDirective.Stop:
            print(f'Stopping {child} reason: {reason}')
            await supervisor.stop_children(child)

        elif directive == SupervisorDirective.Escalate:
            await supervisor.escalate_failure(child, reason)

        else:
            # TODO: raise not handle error
            pass

    def should_stop(self, rs_stats: RestartStatistics):
        if self._max_retries_number == 0:
            return True

        rs_stats.fail()

        if rs_stats.number_of_failures(self._within_timedelta) > self._max_retries_number:
            rs_stats.reset()
            return True

        return False


class OneForOneStrategy(AbstractSupervisorStrategy):

    def __init__(self, decider, max_retries_number, within_timedelta):
        self._decider = decider
        self._max_retries_number = max_retries_number
        self._within_timedelta = within_timedelta

    async def handle_failure(self, supervisor, child: PID,
                       rs_stats: RestartStatistics,
                       reason: Exception):
        directive = self._decider(child, reason)

        if directive == SupervisorDirective.Resume:
            await supervisor.resume_children(child)

        elif directive == SupervisorDirective.Restart:
            if self.should_stop(rs_stats):
                print(f'Restarting {child} reason: {reason}')
                await supervisor.stop_children(child)
            else:
                print(f'Stopping  {child} reason: {reason}')
                await supervisor.restart_children(reason, child)

        elif directive == SupervisorDirective.Stop:
            print(f'Stopping {child} reason: {reason}')
            await supervisor.stop_children(child)

        elif directive == SupervisorDirective.Escalate:
            await supervisor.escalate_failure(child, reason)

        else:
            # TODO: raise not handle error
            pass

    def should_stop(self, rs_stats: RestartStatistics):
        if self._max_retries_number == 0:
            return True

        rs_stats.fail()

        if rs_stats.number_of_failures(self._within_timedelta) > self._max_retries_number:
            rs_stats.reset()
            return True

        return False


class AlwaysRestartStrategy(AbstractSupervisorStrategy):
    def handle_failure(self, supervisor, child: PID,
                       rs_stats: RestartStatistics,
                       reason: Exception):
        supervisor.restart_children(reason, child)


# class Supervision(metaclass=Singleton):
#     @property
#     def default_strategy(self) -> AbstractSupervisorStrategy:
#         return OneForOneStrategy(lambda who, reason: SupervisorDirective.Restart, 10, 10)
#
#     @property
#     def always_restart_strategy(self) -> AlwaysRestartStrategy:
#         return AlwaysRestartStrategy()


class Supervision():
    @property
    def default_strategy(self) -> AbstractSupervisorStrategy:
        return OneForOneStrategy(lambda who, reason: SupervisorDirective.Restart, 10, 10)

    @property
    def always_restart_strategy(self) -> AlwaysRestartStrategy:
        return AlwaysRestartStrategy()


Supervision = Supervision()
