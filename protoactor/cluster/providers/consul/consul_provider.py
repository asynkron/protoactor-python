import asyncio
import base64
from datetime import timedelta, datetime
from typing import List

from protoactor.actor.event_stream import GlobalEventStream
from protoactor.cluster.member_status import AbstractMemberStatusValue, AbstractMemberStatusValueSerializer, \
    MemberStatus
from protoactor.cluster.member_status_events import ClusterTopologyEvent
from protoactor.cluster.providers.abstract_cluster_provider import AbstractClusterProvider
from protoactor.cluster.providers.consul.consul_client import ConsulClient, ConsulClientConfiguration


class ConsulProviderOptions():
    def __init__(self):
        self.service_ttl = timedelta(seconds=10)
        self.refresh_ttl = timedelta(seconds=1)
        self.deregister_critical = timedelta(seconds=30)
        self.blocking_wait_time = timedelta(seconds=20)


class ConsulProvider(AbstractClusterProvider):
    def __init__(self, consul_config: ConsulClientConfiguration,
                 options: ConsulProviderOptions = ConsulProviderOptions()):
        self._config = consul_config
        self._client = None
        self._service_id = None
        self._cluster_name = None
        self._address = None
        self._port = None
        self._kinds = None
        self._service_ttl = options.service_ttl
        self._refresh_ttl = options.refresh_ttl
        self._blocking_wait_time = options.blocking_wait_time
        self._deregister_critical = options.deregister_critical
        self._index = None
        self._shutdown = False
        self._deregistered = False
        self._status_value = None
        self._status_value_serializer = None

    async def register_member_async(self, cluster_name: str, address: str, port: int, kinds: List[str],
                                    status_value: AbstractMemberStatusValue,
                                    status_value_serializer: AbstractMemberStatusValueSerializer) -> None:
        if self._client is None:
            self._client = await ConsulClient.create(self._config)

        self._service_id = f'{cluster_name}@{address}:{port}'
        self._cluster_name = cluster_name
        self._address = address
        self._port = port
        self._kinds = kinds
        self._index = 0
        self._status_value = status_value
        self._status_value_serializer = status_value_serializer

        await self.__register_service_async()
        await self.__register_member_vals_async()

        asyncio.ensure_future(self.__update_ttl())

    async def deregister_member_async(self) -> None:
        await self.__deregister_service_async()
        await self.__deregister_member_vals_async()

        self._deregistered = True

    async def shutdown(self) -> None:
        self._shutdown = True
        if self._deregistered:
            await self.deregister_member_async()

    async def monitor_member_status_changes(self) -> None:
        async def fn():
            while not self._shutdown:
                await self.__notify_statuses()

        asyncio.ensure_future(fn())

    async def __register_service_async(self):
        await self._client.service.register(service_id=self._service_id,
                                            cluster_name=self._cluster_name,
                                            kinds=self._kinds,
                                            address=self._address,
                                            port=self._port,
                                            deregister_critical=self._deregister_critical,
                                            service_ttl=self._service_ttl)

    async def __register_member_vals_async(self):
        key = f'{self._cluster_name}/{self._address}:{self._port}/ID'
        value = str.encode(datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
        await self._client.key_value_storage.create_or_update(key, value)

        if self._status_value is not None:
            status_val_key = f'{self._cluster_name}/{self._address}:{self._port}/StatusValue'
            status_val_value = self._status_value_serializer.to_value_bytes(self._status_value)
            await self._client.key_value_storage.create_or_update(status_val_key, status_val_value)

    async def __update_ttl(self):
        while not self._shutdown:
            await self._client.service.pass_ttl("service:" + self._service_id)
            await asyncio.sleep(self._refresh_ttl.total_seconds())

    async def __deregister_service_async(self):
        await self._client.service.deregister(self._service_id)

    async def update_member_status_value_async(self, status_value: AbstractMemberStatusValue) -> None:
        self._status_value = status_value
        if self._status_value is not None:
            if not self._service_id:
                key = f'{self._cluster_name}/{self._address}:{self._port}/StatusValue'
                value = self._status_value_serializer.to_value_bytes(status_value)
                self._client.key_value_storage.create_or_update(key, value)

    async def __deregister_member_vals_async(self):
        key = f'{self._cluster_name}/{self._address}:{self._port}'
        await self._client.key_value_storage.delete(key)

    async def __notify_statuses(self):
        statuses = await self._client.health.service(self._cluster_name, self._index, self._blocking_wait_time)
        self._index = statuses.last_index
        kv_key = f'{self._cluster_name}/'
        kv = await self._client.key_value_storage.read(kv_key)

        member_ids = {}
        member_status_vals = {}
        for v in kv:
            idx = v['Key'].rfind('/')
            key = v['Key'][0:idx]
            member_type = v['Key'][idx + 1:]
            if member_type == 'ID':
                member_ids[key] = base64.b64decode(v['Value']).decode("UTF-8")
            elif member_type == 'StatusValue':
                member_status_vals[key] = v['Value']

        member_statuses = []
        for v in statuses.response:
            member_id_key = f'{self._cluster_name}/{v.address}:{v.port}'
            if member_id_key in member_ids.keys():
                member_id = member_ids[member_id_key]
                member_status_val = member_status_vals.get(member_id_key)
                member_statuses.append(MemberStatus(member_id, v.address, v.port, v.tags, True,
                                                    self._status_value_serializer.from_value_bytes(member_status_val)))

        for mem_stat in member_statuses:
            if mem_stat.address == self._address and mem_stat.port == self._port:
                self._kinds = mem_stat.kinds
                break

        res = ClusterTopologyEvent(member_statuses)
        await GlobalEventStream.publish(res)
