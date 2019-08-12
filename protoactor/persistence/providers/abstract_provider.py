from abc import abstractmethod, ABCMeta
from typing import Callable, Tuple


class AbstractSnapshotStore(metaclass=ABCMeta):
    @abstractmethod
    async def get_snapshot(self, actor_name: str) -> Tuple[any, int]:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def persist_snapshot(self, actor_name: str, index: int, snapshot: any) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def delete_snapshots(self, actor_name: str, inclusive_to_index: int) -> None:
        raise NotImplementedError("Should Implement this method")


class AbstractEventStore(metaclass=ABCMeta):
    @abstractmethod
    async def get_events(self, actor_name: str, index_start: int, index_end: int,
                         callback: Callable[[any], None]) -> int:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def persist_event(self, actor_name: str, index: int, event: any) -> int:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def delete_events(self, actor_name: str, inclusive_to_index: int) -> None:
        raise NotImplementedError("Should Implement this method")


class AbstractProvider(AbstractEventStore, AbstractSnapshotStore, metaclass=ABCMeta):
    pass
