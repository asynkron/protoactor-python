from typing import List, Callable, Any

from protoactor.actor import PID
from protoactor.actor.actor_context import GlobalRootContext
from protoactor.actor.message_envelope import MessageEnvelope
from protoactor.actor.props import Props
from protoactor.router.hash import HashRing
from protoactor.router.messages import AbstractHashable
from protoactor.router.router_config import GroupRouterConfig, PoolRouterConfig
from protoactor.router.router_state import RouterState


class ConsistentHashGroupRouterConfig(GroupRouterConfig):
    def __init__(self, hash_func: Callable[[str], int], replica_count: int, routees: List[PID]):
        super().__init__()
        if replica_count <= 0:
            raise ValueError('ReplicaCount must be greater than 0')

        self._hash_func = hash_func
        self._replica_count = replica_count
        self._routees = routees

    def create_router_state(self) -> RouterState:
        return ConsistentHashRouterState(self._hash_func, self._replica_count)


class ConsistentHashPoolRouterConfig(PoolRouterConfig):
    def __init__(self, pool_size: int, routee_props: Props, hash_func: Callable[[str], int], replica_count: int):
        super().__init__(pool_size, routee_props)
        if replica_count <= 0:
            raise ValueError('ReplicaCount must be greater than 0')

        self._hash_func = hash_func
        self._replica_count = replica_count

    def create_router_state(self) -> RouterState:
        return ConsistentHashRouterState(self._hash_func, self._replica_count)


class ConsistentHashRouterState(RouterState):
    def __init__(self, hash_func: Callable[[str], int], replica_count: int):
        self._hash_func = hash_func
        self._replica_count = replica_count
        self._hash_ring = None
        self._routee_map = None

    def get_routees(self) -> List[PID]:
        return list(self._routee_map.values())

    def set_routees(self, routees: List[PID]) -> None:
        self._routee_map = {}
        nodes = []

        for pid in routees:
            node_name = pid.to_short_string()
            nodes.append(node_name)
            self._routee_map[node_name] = pid

        self._hash_ring = HashRing(nodes, self._hash_func, self._replica_count)

    async def route_message(self, message: Any) -> None:
        msg, _, _ = MessageEnvelope.unwrap(message)
        if isinstance(msg, AbstractHashable):
            key = msg.hash_by()
            node = self._hash_ring.get_node(key)
            routee = self._routee_map[node]
            await GlobalRootContext.send(routee, message)
        else:
            raise AttributeError('Message of type %s does not implement AbstractHashable' % type(message).__name__)
