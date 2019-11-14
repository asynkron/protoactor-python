import threading
from abc import abstractmethod, ABC

from protoactor.actor import PID, ProcessRegistry
from protoactor.actor.actor_context import AbstractContext, ActorContext
from protoactor.actor.exceptions import ProcessNameExistException
from protoactor.actor.messages import Started
from protoactor.actor.props import Props
from protoactor.router.router_actor import RouterActor
from protoactor.router.router_process import RouterProcess
from protoactor.router.router_state import RouterState


class RouterConfig:
    @abstractmethod
    async def on_started(self, context: AbstractContext, router: RouterState) -> None:
        pass

    @abstractmethod
    def create_router_state(self) -> RouterState:
        pass

    def props(self) -> Props:
        def spawn_router_process(name: str, props: Props, parent: PID) -> PID:
            wg = threading.Event()
            router_state = self.create_router_state()
            p = props.with_producer(lambda: RouterActor(self, router_state, wg))

            ctx = ActorContext(p, parent)
            mailbox = props.mailbox_producer()
            dispatcher = props.dispatcher
            process = RouterProcess(router_state, mailbox, wg)
            pid, absent = ProcessRegistry().try_add(name, process)
            if not absent:
                raise ProcessNameExistException(name, pid)

            ctx.my_self = pid
            mailbox.register_handlers(ctx, dispatcher)
            mailbox.post_system_message(Started())
            mailbox.start()
            wg.wait()

            return pid

        return Props().with_spawner(spawn_router_process)


class GroupRouterConfig(RouterConfig, ABC):
    def __init__(self):
        self._routees = None

    async def on_started(self, context: AbstractContext, router: RouterState) -> None:
        for pid in self._routees:
            await context.watch(pid)
        router.set_routees(self._routees)


class PoolRouterConfig(RouterConfig, ABC):
    def __init__(self, pool_size: int, routee_props: Props):
        self._pool_size = pool_size
        self._routee_props = routee_props

    async def on_started(self, context: AbstractContext, router: RouterState) -> None:
        routees = map(lambda x: context.spawn(self._routee_props), range(self._pool_size))
        router.set_routees(list(routees))
