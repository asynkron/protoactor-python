from abc import ABCMeta, abstractmethod

from .restart_statistics import RestartStatistics
from .pid import PID


class AbstractSupervisorStrategy(metaclass=ABCMeta):

    @abstractmethod
    def handle_failure(self, supervisor, child: PID, rs_stats: RestartStatistics, reason: Exception, message: object):
        raise NotImplementedError("Should Implement this method")