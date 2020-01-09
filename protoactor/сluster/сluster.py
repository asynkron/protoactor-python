import asyncio
from datetime import timedelta
from threading import RLock
from typing import Callable, Tuple, List, Optional

from protoactor.actor import ProcessRegistry, PID
from protoactor.actor.actor import Actor, AbstractContext
from protoactor.actor.actor_context import GlobalRootContext
from protoactor.actor.cancel_token import CancelToken
from protoactor.actor.event_stream import GlobalEventStream
from protoactor.actor.messages import Started
from protoactor.actor.props import Props
from protoactor.actor.protos_pb2 import Terminated
from protoactor.actor.supervision import Supervision
from protoactor.remote.messages import EndpointTerminatedEvent
from protoactor.remote.protos_remote_pb2 import ActorPidRequest, ActorPidResponse
from protoactor.remote.remote import RemoteConfig, Remote
from protoactor.remote.response import ResponseStatusCode
from protoactor.remote.serialization import Serialization
from protoactor.сluster.member_status import AbstractMemberStatusValue, AbstractMemberStatusValueSerializer, \
    NullMemberStatusValueSerializer, MemberStatus
from protoactor.сluster.member_status_events import ClusterTopologyEvent, MemberJoinedEvent, MemberLeftEvent, \
    MemberRejoinedEvent, AbstractMemberStatusEvent
from protoactor.сluster.member_strategy import SimpleMemberStrategy, AbstractMemberStrategy
from protoactor.сluster.pid_cache import PidCache
from protoactor.сluster.protos_pb2 import TakeOwnership, DESCRIPTOR
from protoactor.сluster.providers.abstract_cluster_provider import AbstractClusterProvider


class MemberList:
    def __init__(self):
        self._logger = None
        self._lock = RLock()
        self._members = {}
        self._member_strategy_by_kind = {}
        self._cluster_topology_evn_sub = None

    def setup(self) -> None:
        self._cluster_topology_evn_sub = GlobalEventStream.subscribe(self.update_cluster_topology, ClusterTopologyEvent)

    def stop(self) -> None:
        GlobalEventStream.unsubscribe(self._cluster_topology_evn_sub.id)

    def get_members(self, kind: str) -> List[str]:
        with self._lock:
            member_strategy = self._member_strategy_by_kind.get(kind, None)
            if member_strategy is not None:
                members = []
                for member in member_strategy.get_all_members:
                    if member.alive:
                        members.append(member.address)
                    if len(members) > 0:
                        return members
                    return []

    def get_partition(self, name: str, kind: str) -> str:
        with self._lock:
            member_strategy = self._member_strategy_by_kind.get(kind, None)
            if member_strategy is not None:
                return member_strategy.get_partition(name)
            return ''

    def get_activator(self, kind: str) -> str:
        with self._lock:
            member_strategy = self._member_strategy_by_kind.get(kind, None)
            if member_strategy is not None:
                return member_strategy.get_activator()
            return ''

    async def update_cluster_topology(self, msg: ClusterTopologyEvent):
        with self._lock:
            new_members_address = []
            for status in msg.statuses:
                new_members_address.append(status.address)

            for address, old in self._members.items():
                if address not in new_members_address:
                    await self.update_and_notify(None, old)

            for new in msg.statuses:
                old = self._members.get(new.address)
                self._members[new.address] = new
                await self.update_and_notify(new, old)

    async def update_and_notify(self, new: MemberStatus, old: MemberStatus):
        if new is None and old is None:
            return

        if new is None:
            # update MemberStrategy
            for kind in old.kinds:
                member_strategy = self._member_strategy_by_kind.get(kind, None)
                if member_strategy is not None:
                    member_strategy.remove_member(old)
                    if len(member_strategy.get_all_members) == 0:
                        del self._member_strategy_by_kind[kind]

            # notify left
            left = MemberLeftEvent(old.host, old.port, old.kinds)
            await GlobalEventStream.publish(left)
            del self._members[old.address]

            endpoint_terminated = EndpointTerminatedEvent(address=old.address)
            await GlobalEventStream.publish(endpoint_terminated)
            return

        if old is None:
            # update MemberStrategy
            for kind in new.kinds:
                if kind not in self._member_strategy_by_kind.keys():
                    self._member_strategy_by_kind[kind] = Cluster.config.member_strategy_builder(kind)
                self._member_strategy_by_kind[kind].add_member(new)

            # notify joined
            joined = MemberJoinedEvent(new.host, new.port, new.kinds)
            await GlobalEventStream.publish(joined)
            return

        # update MemberStrategy
        if new.alive != old.alive or \
                new.member_id != old.member_id or \
                new.status_value is not None and \
                not new.status_value.is_same(old.status_value):
            for kind in new.kinds:
                member_strategy = self._member_strategy_by_kind.get(kind, None)
                if member_strategy is not None:
                    member_strategy.update_member(new)

        # notify changes
        if new.member_id != old.member_id:
            rejoined = MemberRejoinedEvent(new.host, new.port, new.kinds)
            await GlobalEventStream.publish(rejoined)


class SpawningProcess():
    def __init__(self, spawning_address: str):
        self._spawning_address = spawning_address
        self._loop = asyncio.get_event_loop()
        self._future = self._loop.create_future()

    @property
    def task(self) -> asyncio.Future:
        return self._future

    @property
    def spawning_address(self) -> str:
        return self._spawning_address

    def set_result(self, msg):
        self._future.set_result(msg)


class Partition():
    def __init__(self):
        self._kind_map = {}
        self._member_status_sub = None

    async def setup(self, kinds: List[str]):
        for kind in kinds:
            pid = await self.spawn_partition_actor(kind)
            self._kind_map[kind] = pid

        GlobalEventStream.subscribe(self.__process_member_status_event, AbstractMemberStatusEvent)

    @staticmethod
    async def spawn_partition_actor(kind: str) -> PID:
        props = Props.from_producer(lambda: PartitionActor(kind)) \
            .with_guardian_supervisor_strategy(Supervision.always_restart_strategy)

        return GlobalRootContext.spawn_named(props, 'partition-' + kind)

    async def stop(self) -> None:
        for kind in self._kind_map.values():
            await GlobalRootContext.stop(kind)
        self._kind_map.clear()
        GlobalEventStream.unsubscribe(self._member_status_sub.id)

    @staticmethod
    def partition_for_kind(address: str, kind: str) -> PID:
        return PID(address=address, id='partition-' + kind)

    async def __process_member_status_event(self, msg: AbstractMemberStatusEvent) -> None:
        for kind in msg.kinds:
            if kind in self._kind_map:
                await GlobalRootContext.send(self._kind_map[kind], msg)


class PartitionActor(Actor):
    def __init__(self, kind: str):
        self._kind = kind
        self._logger = None

        self._partition = {}
        self._reverse_partition = {}
        self._spawning_procs = {}

    async def receive(self, context: AbstractContext):
        msg = context.message
        if isinstance(msg, Started):
            # self._logger.log_debug('Started PartitionActor ' + self._kind)
            pass
        elif isinstance(msg, ActorPidRequest):
            await self._spawn(msg, context)
        elif isinstance(msg, Terminated):
            self._terminated(msg)
        elif isinstance(msg, TakeOwnership):
            await self._take_ownership(msg, context)
        elif isinstance(msg, MemberJoinedEvent):
            await self._member_joined(msg, context)
        elif isinstance(msg, MemberRejoinedEvent):
            self._member_rejoined(msg)
        elif isinstance(msg, MemberLeftEvent):
            await self._member_left(msg, context)

    def _terminated(self, msg: Terminated):
        key = next(iter([k for k, v in self._partition.items() if v == msg.who]), None)
        if key is not None:
            del self._partition[key]

    async def _take_ownership(self, msg: TakeOwnership, context: AbstractContext):
        address = MemberList.get_partition(msg.name, self._kind)
        if not address and address != ProcessRegistry().address:
            owner = Partition.partition_for_kind(address, self._kind)
            await context.send(owner, msg)
        else:
            self._logger.log_debug(f'Kind {self._kind} Member Left {msg.address}')
            self._partition[msg.name] = msg.pid
            await context.watch(msg.pid)

    async def _member_left(self, msg: MemberLeftEvent, context: AbstractContext):
        self._logger.log_information(f'Kind {self._kind} Member Left {msg.address}')

        if msg.address == ProcessRegistry().address:
            for actor_id, _ in self._partition:
                address = MemberList.get_partition(actor_id, self._kind)
                if not address:
                    await self._transfer_ownership(actor_id, address, context)

            for actor_id, pid in self._partition:
                if pid.address == msg.address:
                    del self._partition[actor_id]

            for _, sp in self._spawning_procs:
                if sp.spawning_address == msg.address:
                    sp.set_result(ActorPidResponse.Unavailable)

    def _member_rejoined(self, msg: MemberRejoinedEvent):
        self._logger.log_information(f'Kind {self._kind} Member Joined {msg.address}')

        for actor_id, pid in self._partition:
            if pid.address == msg.address:
                del self._partition[actor_id]

        for _, sp in self._spawning_procs:
            if sp.spawning_address == msg.address:
                sp.set_result(ActorPidResponse.Unavailable)

    async def _member_joined(self, msg: MemberJoinedEvent, context: AbstractContext):
        # self._logger.log_information('Kind %s Member Joined %s' % (self._kind, msg.address))

        for actor_id, _ in self._partition:
            address = MemberList.get_partition(actor_id, self._kind)
            if not address and address != ProcessRegistry().address:
                await self._transfer_ownership(actor_id, address, context)

        for actor_id, sp in self._spawning_procs:
            address = MemberList.get_partition(actor_id, self._kind)
            if not address and address != ProcessRegistry().address:
                sp.set_result(ActorPidResponse.Unavailable)

    async def _transfer_ownership(self, actor_id: str, address: str, context: AbstractContext):
        pid = self._partition[actor_id]
        owner = Partition.partition_for_kind(address, self._kind)
        await context.send(owner, TakeOwnership(name=actor_id, pid=pid))

        del self._partition[actor_id]
        await context.unwatch(pid)

    async def _spawn(self, msg: ActorPidRequest, context: AbstractContext):
        # Check if exist in current partition dictionary
        pid = self._partition.get(msg.name, None)
        if pid is not None:
            await context.respond(ActorPidResponse(pid=pid))
            return

        # Check if is spawning, if so just await spawning finish.
        spawning = self._spawning_procs.get(msg.name, None)
        if spawning is not None:
            async def fn(rst):
                if rst.exception() is not None:
                    await context.respond(ActorPidResponse.Err)
                else:
                    await context.respond(rst.result())

            context.reenter_after(spawning.task, fn)
            return

        # Get activator
        activator = MemberList.get_activator(msg.kind)
        if not activator:
            # No activator currently available, return unavailable
            self._logger.log_debug('No members currently available')
            await context.respond(ActorPidResponse.Unavailable)
            return

        # Create SpawningProcess and cache it in spawning dictionary.
        spawning = SpawningProcess(activator)
        self._spawning_procs[msg.name] = spawning

        async def fn(rst):
            del self._spawning_procs[msg.name]

            # Check if exist in current partition dictionary
            # This is necessary to avoid race condition during partition map transfering.
            pid = self._partition.get(msg.name, None)
            if pid is not None:
                await context.respond(ActorPidResponse(pid=pid))
                return

            # Check if process is faulted
            if rst.exception() is not None:
                await context.respond(ActorPidResponse.Err)
                return

            pid_resp = rst.result()
            if pid_resp.status_code == ResponseStatusCode.OK:
                pid = pid_resp.pid
                self._partition[msg.name] = pid
                await context.watch(pid)
            await context.respond(pid_resp)

        # Await SpawningProcess
        # asyncio.ensure_future(fn())
        context.reenter_after(spawning.task, fn)
        # await self.__spawning(msg, activator, 3, spawning)
        asyncio.ensure_future(self.__spawning(msg, activator, 3, spawning))

    async def __spawning(self, req: ActorPidRequest, activator: Optional[str], retry_left: int,
                         spawning: SpawningProcess):
        if not activator:
            activator = MemberList.get_activator(req.kind)
            if not activator:
                self._logger.log_debug('No activator currently available')
                spawning.set_result(ActorPidResponse.Unavailable)
                return

        try:
            pid_resp = await Remote().spawn_named_async(activator, req.name, req.kind, Cluster.config.timeout_timespan)
        except TimeoutError:
            spawning.set_result(ActorPidResponse.TimeOut)
            return
        except Exception:
            spawning.set_result(ActorPidResponse.Err)
            return

        if pid_resp.status_code == ResponseStatusCode.Unavailable and retry_left != 0:
            await self.__spawning(req, None, (retry_left - 1), spawning)
            return

        spawning.set_result(pid_resp)


class ClusterConfig:
    def __init__(self, name: str, address: str, port: int, cluster_provider: AbstractClusterProvider):
        if name is None:
            raise ValueError('name is empty')
        self._name = name

        if address is None:
            raise ValueError('address is empty')
        self._address = address
        self._port = port

        if cluster_provider is None:
            raise ValueError('cluster provider is empty')
        self._cluster_provider = cluster_provider

        self._remote_config = RemoteConfig()
        self._timeout_timespan = timedelta(seconds=5)
        self._initial_member_status_value = None
        self._member_status_value_serializer = NullMemberStatusValueSerializer()
        self._member_strategy_builder = lambda kind: SimpleMemberStrategy()

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address

    @property
    def port(self) -> int:
        return self._port

    @property
    def cluster_provider(self) -> AbstractClusterProvider:
        return self._cluster_provider

    @property
    def remote_config(self) -> RemoteConfig:
        return self._remote_config

    @property
    def timeout_timespan(self) -> timedelta:
        return self._timeout_timespan

    @property
    def initial_member_status_value(self) -> AbstractMemberStatusValue:
        return self._initial_member_status_value

    @property
    def member_status_value_serializer(self) -> AbstractMemberStatusValueSerializer:
        return self._member_status_value_serializer

    @property
    def member_strategy_builder(self) -> Callable[[str], AbstractMemberStrategy]:
        return self._member_strategy_builder

    def with_remote_config(self, remote_config: RemoteConfig) -> 'ClusterConfig':
        self._remote_config = remote_config
        return self

    def with_timeout_seconds(self, timeout_seconds: int) -> 'ClusterConfig':
        self._timeout_timespan = timedelta(seconds=timeout_seconds)
        return self

    def with_initial_member_status_value(self, status_value: AbstractMemberStatusValue) -> 'ClusterConfig':
        self._initial_member_status_value = status_value
        return self

    def with_member_status_value_serializer(self, serializer: AbstractMemberStatusValueSerializer) -> 'ClusterConfig':
        self._member_status_value_serializer = serializer
        return self

    def with_member_strategy_builder(self, builder: Callable[[str], AbstractMemberStrategy]) -> 'ClusterConfig':
        self._member_strategy_builder = builder
        return self


class Cluster:
    def __init__(self):
        self._logger = None
        self._config = None

    @property
    def config(self) -> ClusterConfig:
        return self._config

    async def start(self, cluster_name: str, address: str, port: int,
                    cluster_provider: AbstractClusterProvider) -> None:
        await self.start_with_config(ClusterConfig(cluster_name, address, port, cluster_provider))

    async def start_with_config(self, config: ClusterConfig) -> None:
        self._config = config

        Remote().start(self._config.address, self._config.port, self._config.remote_config)

        Serialization().register_file_descriptor(DESCRIPTOR)
        # self._logger.log_information('Starting Proto.Actor cluster')
        host, port = self.__parse_address(ProcessRegistry().address)
        kinds = Remote().get_known_kinds()

        await Partition.setup(kinds)
        await PidCache().setup()
        MemberList.setup()

        await self._config.cluster_provider.register_member_async(self._config.name, host, port, kinds,
                                                                  self._config.initial_member_status_value,
                                                                  self._config.member_status_value_serializer)

        await self._config.cluster_provider.monitor_member_status_changes()
        # self._logger.log_information('Started Cluster')

    async def shutdown(self, gracefull: bool = True) -> None:
        if gracefull:
            await self._config.cluster_provider.shutdown()
            # This is to wait ownership transfering complete.
            await asyncio.sleep(2)
            MemberList.stop()
            await PidCache().stop()
            await Partition.stop()

        Remote().shutdown(gracefull)
        self._logger.log_information('Stopped Cluster')

    async def get_async(self, name: str, kind: str, cancellation_token: CancelToken = None) -> \
            Tuple[PID, ResponseStatusCode]:

        pid, ok = PidCache().get_cache(name)
        if ok:
            return pid, ResponseStatusCode.OK

        address = MemberList.get_partition(name, kind)
        if not address:
            return None, ResponseStatusCode.Unavailable

        remote_pid = Partition.partition_for_kind(address, kind)
        req = ActorPidRequest(kind=kind, name=name)

        try:
            if cancellation_token is None:
                resp = await GlobalRootContext.request_future(remote_pid, req, self._config.timeout_timespan)
            else:
                resp = await GlobalRootContext.request_future(remote_pid, req, cancellation_token=cancellation_token)
            status = ResponseStatusCode(resp.status_code)

            if status == ResponseStatusCode.OK:
                await PidCache().add_cache(name, resp.pid)
                return resp.pid, status
            return resp.pid, status
        except TimeoutError:
            return None, ResponseStatusCode.Timeout
        except Exception:
            return None, ResponseStatusCode.Error

    @staticmethod
    def __parse_address(address: str) -> Tuple[str, int]:
        parts = address.split(':')
        host = parts[0]
        port = int(parts[1])
        return host, port


MemberList = MemberList()

Partition = Partition()

Cluster = Cluster()
