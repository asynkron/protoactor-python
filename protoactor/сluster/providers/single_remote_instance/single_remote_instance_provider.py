import asyncio
from datetime import timedelta
from typing import List

from protoactor.actor.actor import AbstractContext, GlobalRootContext
from protoactor.actor.event_stream import GlobalEventStream
from protoactor.actor.props import Props
from protoactor.mailbox.dispatcher import Dispatchers
from protoactor.remote.remote import Remote
from protoactor.remote.serialization import Serialization
from protoactor.сluster.member_status import AbstractMemberStatusValue, AbstractMemberStatusValueSerializer, \
    MemberStatus
from protoactor.сluster.member_status_events import ClusterTopologyEvent
from protoactor.сluster.providers.abstract_cluster_provider import AbstractClusterProvider
from protoactor.сluster.providers.single_remote_instance.protos_pb2 import GetKinds, GetKindsResponse, DESCRIPTOR


class SingleRemoteInstanceProvider(AbstractClusterProvider):
    def __init__(self, server_host: str, server_port: int):
        self._kinds_responder = 'remote_kinds_responder'
        self._timeout = timedelta(seconds=10)

        self._server_host = server_host
        self._server_port = server_port
        self._server_address = '%s:%s' % (server_host, str(server_port))

        self._kinds = []
        self._ok_status = None
        self._ko_status = None

        self._is_server = None
        self._shutdown = None

        async def fn(ctx: AbstractContext):
            if isinstance(ctx.message, GetKinds) and ctx.sender is not None:
                await ctx.respond(GetKindsResponse(kinds=self._kinds))

        props = Props.from_func(fn)

        Serialization().register_file_descriptor(DESCRIPTOR)
        Remote().register_known_kind(self._kinds_responder, props)

    async def register_member_async(self, cluster_name: str, host: str, port: int, kinds: List[str],
                                    status_value: AbstractMemberStatusValue,
                                    serializer: AbstractMemberStatusValueSerializer) -> None:
        self._kinds = kinds
        self._ok_status = serializer.from_value_bytes('Ok!'.encode())
        self._ko_status = serializer.from_value_bytes('Ko!'.encode())

        self._is_server = host == self._server_host and port == self._server_port

    async def deregister_member_async(self) -> None:
        pass

    def monitor_member_status_changes(self) -> None:
        async def fn():
            while not self._shutdown:
                await self.__notify_statuses()

        Dispatchers().default_dispatcher.schedule(fn)

    async def update_member_status_value_async(self, status_value: AbstractMemberStatusValue) -> None:
        pass

    def shutdown(self) -> None:
        self._shutdown = True

    async def __notify_statuses(self):
        status = None
        if self._is_server:
            status = MemberStatus(self._server_address, self._server_host, self._server_port, self._kinds, True,
                                  self._ok_status)
        else:
            responder = await Remote().spawn_named_async(self._server_address, self._kinds_responder,
                                                         self._kinds_responder, self._timeout)
            if responder.pid is not None:
                try:
                    response = await GlobalRootContext.request_future(responder.pid, GetKinds(), self._timeout)
                    status = MemberStatus(self._server_address, self._server_host, self._server_port, response.kinds,
                                          True, self._ok_status)
                except TimeoutError:
                    status = MemberStatus(self._server_address, self._server_host, self._server_port, [], True,
                                          self._ko_status)
            else:
                status = MemberStatus(self._server_address, self._server_host, self._server_port, [], False,
                                      self._ko_status)

        event = ClusterTopologyEvent([status])
        await GlobalEventStream.publish(event)
        await asyncio.sleep(60)