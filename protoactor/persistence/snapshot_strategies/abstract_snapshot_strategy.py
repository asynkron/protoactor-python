from abc import abstractmethod, ABCMeta

from protoactor.persistence.messages import PersistedEvent


class AbstractSnapshotStrategy(metaclass=ABCMeta):
    @abstractmethod
    def should_take_snapshot(self, persisted_event: PersistedEvent) -> bool:
        raise NotImplementedError("Should Implement this method")
