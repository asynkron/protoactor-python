from threading import Event

from protoactor.actor.actor_context import Actor, AbstractContext
from protoactor.actor.messages import Started
from protoactor.actor.protos_pb2 import Terminated
from protoactor.router.messages import AddRoutee, RemoveRoutee, BroadcastMessage, GetRoutees, Routees, \
    RouterManagementMessage
from protoactor.router.router_state import RouterState

is_import = False
if is_import:
    from protoactor.router.router_config import RouterConfig


class RouterActor(Actor):
    def __init__(self, config: 'RouterConfig', router_state: RouterState, wg: Event):
        self._config = config
        self._router_state = router_state
        self._wg = wg

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if isinstance(msg, Started):
            await self.process_started_message(context)
        elif isinstance(msg, Terminated):
            await self.process_terminated_message(context)
        elif isinstance(msg, RouterManagementMessage):
            await self.process_router_management_message(context)
        else:
            await self.process_message(context)

    async def process_started_message(self, context):
        await self._config.on_started(context, self._router_state)
        self._wg.set()

    async def process_terminated_message(self, context):
        pass

    async def process_router_management_message(self, context):
        msg = context.message
        if isinstance(msg, AddRoutee):
            routees = self._router_state.get_routees()
            if msg.pid not in routees:
                await context.watch(msg.pid)
                routees.append(msg.pid)
                self._router_state.set_routees(routees)
            self._wg.set()
        elif isinstance(msg, RemoveRoutee):
            routees = self._router_state.get_routees()
            if msg.pid in routees:
                await context.unwatch(msg.pid)
                routees.remove(msg.pid)
                self._router_state.set_routees(routees)
            self._wg.set()
        elif isinstance(msg, BroadcastMessage):
            for routee in self._router_state.get_routees():
                await context.request(routee, msg.message)
            self._wg.set()
        elif isinstance(msg, GetRoutees):
            self._wg.set()
            routees = self._router_state.get_routees()
            await context.respond(Routees(routees))

    async def process_message(self, context):
        await self._router_state.route_message(context.message)
        self._wg.set()
