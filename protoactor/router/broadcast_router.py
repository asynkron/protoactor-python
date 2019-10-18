from typing import List, Any, Iterable

from protoactor.actor import PID
from protoactor.actor.actor import GlobalRootContext
from protoactor.actor.props import Props
from protoactor.router.router_config import GroupRouterConfig, PoolRouterConfig
from protoactor.router.router_state import RouterState


class BroadcastGroupRouterConfig(GroupRouterConfig):
    def __init__(self, routees: List[PID]):
        super().__init__()
        self._routees = routees

    def create_router_state(self) -> RouterState:
        return BroadcastRouterState()


class BroadcastPoolRouterConfig(PoolRouterConfig):
    def __init__(self, pool_size: int, routee_props: Props):
        super().__init__(pool_size, routee_props)

    def create_router_state(self) -> RouterState:
        return BroadcastRouterState()


class BroadcastRouterState(RouterState):
    def __init__(self):
        self._routees = None

    def get_routees(self) -> List[PID]:
        return list(self._routees)

    def set_routees(self, routees: Iterable[PID]) -> None:
        self._routees = routees

    async def route_message(self, message: Any) -> None:
        for pid in self._routees:
            await GlobalRootContext.send(pid, message)