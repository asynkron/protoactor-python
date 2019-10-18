from typing import Tuple

from protoactor.actor.actor import Actor, AbstractContext, GlobalRootContext
from protoactor.actor.event_stream import GlobalEventStream
from protoactor.actor.messages import Started
from protoactor.actor.props import Props
from protoactor.actor.protos_pb2 import Terminated, PID
from protoactor.actor.supervision import Supervision
from protoactor.actor.utils import Singleton
from protoactor.сluster.member_status_events import AbstractMemberStatusEvent, MemberLeftEvent, MemberRejoinedEvent
from protoactor.сluster.messages import WatchPidRequest


class PidCache(metaclass=Singleton):
    def __init__(self):
        self._watcher = None
        self._cluster_topology_evn_sub = None
        self._cache = {}
        self._reverse_cache = {}

    async def setup(self) -> None:
        props = Props.from_producer(lambda: PidCacheWatcher()) \
            .with_guardian_supervisor_strategy(Supervision.always_restart_strategy)

        self._watcher = GlobalRootContext.spawn_named(props, 'PidCacheWatcher')
        self._cluster_topology_evn_sub = GlobalEventStream.subscribe(self.process_member_status_event,
                                                                     type(AbstractMemberStatusEvent))

    async def stop(self) -> None:
        await GlobalRootContext.stop(self._watcher)
        GlobalEventStream.unsubscribe(self._cluster_topology_evn_sub.id)

    def process_member_status_event(self, evn: AbstractMemberStatusEvent) -> None:
        if isinstance(evn, MemberLeftEvent) or isinstance(evn, MemberRejoinedEvent):
            self.remove_cache_by_member_address(evn.address)

    def get_cache(self, name: str) -> Tuple[PID, bool]:
        if name in self._cache.keys():
            return self._cache[name], True
        else:
            return None, False

    async def add_cache(self, name: str, pid: PID) -> bool:
        if name not in self._cache.keys():
            key = pid.to_short_string()
            self._cache[name] = pid
            self._reverse_cache[key] = name

            await GlobalRootContext.send(self._watcher, WatchPidRequest(pid))
            return True
        return False

    def remove_cache_by_pid(self, pid: PID) -> None:
        key = pid.to_short_string()
        if key in self._reverse_cache:
            name = self._reverse_cache[key]
            del self._reverse_cache[key]
            del self._cache[name]

    def remove_cache_by_name(self, name: str) -> None:
        if name in self._cache:
            key = self._cache[name]
            del self._reverse_cache[key]
            del self._cache[name]

    def remove_cache_by_member_address(self, member_address: str) -> None:
        for name, pid in self._cache.items():
            if pid.address == member_address:
                key = pid.to_short_string()
                del self._reverse_cache[key]
                del self._cache[name]


class PidCacheWatcher(Actor):
    def __init__(self):
        self._logger = None

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if isinstance(msg, Started):
            # self._logger.log_debug('Started PidCacheWatcher')
            pass
        elif isinstance(msg, WatchPidRequest):
            await context.watch(msg.pid)
        elif isinstance(msg, Terminated):
            PidCache().remove_cache_by_pid(msg.who)
