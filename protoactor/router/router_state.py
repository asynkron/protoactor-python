from abc import abstractmethod
from typing import Iterable, Any, List

from protoactor.actor import PID


class RouterState:
    @abstractmethod
    def get_routees(self) -> List[PID]:
        pass

    @abstractmethod
    def set_routees(self, routees: Iterable[PID]) -> None:
        pass

    @abstractmethod
    async def route_message(self, message: Any) -> None:
        pass
