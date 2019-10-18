import random
from typing import List, Any

from protoactor.actor import PID
from protoactor.actor.actor import GlobalRootContext
from protoactor.actor.props import Props
from protoactor.router.router_config import GroupRouterConfig, PoolRouterConfig
from protoactor.router.router_state import RouterState


class RandomGroupRouterConfig(GroupRouterConfig):
    def __init__(self, routees: List[PID], seed: int = None):
        super().__init__()
        self._routees = routees
        self._seed = seed

    def create_router_state(self) -> RouterState:
        return RandomRouterState(self._seed)


class RandomPoolRouterConfig(PoolRouterConfig):
    def __init__(self, pool_size: int, routee_props: Props, seed: int = None):
        super().__init__(pool_size, routee_props)
        self._seed = seed

    def create_router_state(self) -> RouterState:
        return RandomRouterState(self._seed)


class RandomRouterState(RouterState):
    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
        self._routees = None

    def get_routees(self) -> List[PID]:
        return list(self._routees)

    def set_routees(self, routees: List[PID]) -> None:
        self._routees = routees

    async def route_message(self, message: Any) -> None:
        i = random.randint(0, len(self._routees) - 1)
        pid = self._routees[i]
        await GlobalRootContext.send(pid, message)
