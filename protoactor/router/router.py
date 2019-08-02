from typing import Callable, List

from protoactor.actor import PID
from protoactor.actor.props import Props
from protoactor.router.broadcast_router import BroadcastGroupRouterConfig, BroadcastPoolRouterConfig
from protoactor.router.consistent_hash_group_router import ConsistentHashGroupRouterConfig, \
    ConsistentHashPoolRouterConfig
from protoactor.router.hash import MD5Hasher
from protoactor.router.random_router import RandomGroupRouterConfig, RandomPoolRouterConfig
from protoactor.router.round_robin_router import RoundRobinGroupRouterConfig, RoundRobinPoolRouterConfig


class Router:
    @staticmethod
    def new_broadcast_group(routees: List[PID]) -> Props:
        return BroadcastGroupRouterConfig(routees).props()

    @staticmethod
    def new_consistent_hash_group(routees: List[PID],
                                  hash_func: Callable[[str], int] = None,
                                  replica_count: int = None) -> Props:

        if hash_func is None and replica_count is None:
            return ConsistentHashGroupRouterConfig(MD5Hasher.hash, 100, routees).props()
        return ConsistentHashGroupRouterConfig(hash_func, replica_count, routees).props()

    @staticmethod
    def new_random_group(routees: List[PID], seed: int = None) -> Props:
        return RandomGroupRouterConfig(routees, seed).props()

    @staticmethod
    def new_round_robin_group(routees: List[PID]) -> Props:
        return RoundRobinGroupRouterConfig(routees).props()

    @staticmethod
    def new_broadcast_pool(props: Props, pool_size: int) -> Props:
        return BroadcastPoolRouterConfig(pool_size, props).props()

    @staticmethod
    def new_consistent_hash_pool(props: Props,
                                 pool_size: int,
                                 hash_func: Callable[[str], int] = None,
                                 replica_count: int = 100) -> Props:

        if hash_func is None:
            return ConsistentHashPoolRouterConfig(pool_size, props, MD5Hasher.hash, replica_count).props()
        return ConsistentHashPoolRouterConfig(pool_size, props, hash_func, replica_count).props()

    @staticmethod
    def new_random_pool(props: Props, pool_size: int, seed: int = None) -> Props:
        return RandomPoolRouterConfig(pool_size, props, seed).props()

    @staticmethod
    def new_round_robin_pool(props: Props, pool_size: int) -> Props:
        return RoundRobinPoolRouterConfig(pool_size, props).props()
