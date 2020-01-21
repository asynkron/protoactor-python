import logging
from abc import ABCMeta, abstractmethod
from datetime import timedelta
from enum import Enum
from traceback import TracebackException
from typing import List, Callable, Optional, Any

from protoactor.actor.protos_pb2 import PID
from . import log
from .restart_statistics import RestartStatistics


class SupervisorDirective(Enum):
    Resume = 0
    Restart = 1
    Stop = 2
    Escalate = 3


Decider = Callable[[PID, Exception], SupervisorDirective]


class AbstractSupervisor(metaclass=ABCMeta):

    @abstractmethod
    async def escalate_failure(self, reason: Exception, message: Any) -> None:
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
    async def handle_failure(self, supervisor, child: PID, rs_stats: RestartStatistics, reason: Exception,
                             message: Any):
        raise NotImplementedError("Should Implement this method")


class AllForOneStrategy(AbstractSupervisorStrategy):
    def __init__(self, decider: Decider, max_retries_number: int, within_timedelta: Optional[timedelta]):
        self._decider = decider
        self._max_retries_number = max_retries_number
        self._within_timedelta = within_timedelta
        self._logger = log.create_logger(logging.INFO, context=AllForOneStrategy)

    async def handle_failure(self, supervisor, child: PID,
                             rs_stats: RestartStatistics,
                             reason: Exception,
                             message: Any):
        directive = self._decider(child, reason)
        exp = "".join(TracebackException.from_exception(reason).format())

        if directive == SupervisorDirective.Resume:
            self._logger.info(f'Resuming {child.to_short_string()} Reason {exp}')
            await supervisor.resume_children(child)
        elif directive == SupervisorDirective.Restart:
            if self.should_stop(rs_stats):
                self._logger.info(f'Stopping {child.to_short_string()} Reason {exp}')
                await supervisor.stop_children(*supervisor.children())
            else:
                self._logger.info(f'Restarting {child.to_short_string()} Reason {exp}')
                await supervisor.restart_children(reason, supervisor.children())
        elif directive == SupervisorDirective.Stop:
            self._logger.info(f'Stopping {child.to_short_string()} Reason {exp}')
            await supervisor.stop_children(child)

        elif directive == SupervisorDirective.Escalate:
            await supervisor.escalate_failure(reason, message)
        else:
            raise ValueError('Argument Out Of Range')

    def should_stop(self, rs: RestartStatistics):
        if self._max_retries_number == 0:
            return True

        rs.fail()

        if rs.number_of_failures(self._within_timedelta) > self._max_retries_number:
            rs.reset()
            return True
        return False


class OneForOneStrategy(AbstractSupervisorStrategy):
    def __init__(self, decider: Decider, max_retries_number: int, within_timedelta: Optional[timedelta]):
        self._decider = decider
        self._max_retries_number = max_retries_number
        self._within_timedelta = within_timedelta
        self._logger = log.create_logger(logging.INFO, context=OneForOneStrategy)

    async def handle_failure(self, supervisor, child: PID,
                             rs_stats: RestartStatistics,
                             reason: Exception,
                             message: Any):
        directive = self._decider(child, reason)
        exp = "".join(TracebackException.from_exception(reason).format())

        if directive == SupervisorDirective.Resume:
            await supervisor.resume_children(child)
        elif directive == SupervisorDirective.Restart:
            if self.should_stop(rs_stats):
                self._logger.info(f'Stopping {child.to_short_string()} Reason {exp}')
                await supervisor.stop_children(child)
            else:
                self._logger.info(f'Restarting {child.to_short_string()} Reason {exp}')
                await supervisor.restart_children(reason, child)
        elif directive == SupervisorDirective.Stop:
            self._logger.info(f'Stopping {child.to_short_string()} Reason {exp}')
            await supervisor.stop_children(child)
        elif directive == SupervisorDirective.Escalate:
            await supervisor.escalate_failure(reason, message)
        else:
            raise ValueError('Argument Out Of Range')

    def should_stop(self, rs: RestartStatistics):
        if self._max_retries_number == 0:
            return True

        rs.fail()

        if rs.number_of_failures(self._within_timedelta) > self._max_retries_number:
            rs.reset()
            return True
        return False


class AlwaysRestartStrategy(AbstractSupervisorStrategy):
    def handle_failure(self, supervisor, child: PID,
                       rs_stats: RestartStatistics,
                       reason: Exception,
                       message: Any):
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
        return OneForOneStrategy(lambda who, reason: SupervisorDirective.Restart, 10, timedelta(seconds=10))

    @property
    def always_restart_strategy(self) -> AlwaysRestartStrategy:
        return AlwaysRestartStrategy()


Supervision = Supervision()
