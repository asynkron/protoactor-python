import datetime
import json
from datetime import timedelta
from typing import List

import aiohttp


class ConsulClientConfiguration:
    def __init__(self, address: str, datacenter: str = 'dc1'):
        self.address = address
        self.datacenter = datacenter


class ServiceEntry:
    def __init__(self, address: str, port: int, tags: List[str]):
        self.address = address
        self.port = port
        self.tags = tags


class QueryResult:
    def __init__(self, last_index: int, response: List[ServiceEntry]):
        self.last_index = last_index
        self.response = response


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.timedelta):
            if obj.total_seconds() < 60:
                return str(int(obj.total_seconds())) + 's'
            else:
                return str(obj.total_seconds() / 60) + 'm'

        return super(DateTimeEncoder, self).default(obj)


class ServiceEndpoint:
    def __init__(self, client: aiohttp.ClientSession, url: str):
        self._client = client
        self._base_url = url

    async def register(self, service_id: str,
                       cluster_name: str,
                       kinds: List[str],
                       address: str,
                       port: int,
                       deregister_critical: timedelta,
                       service_ttl: timedelta) -> None:

        data = json.dumps({'ID': service_id,
                           'Name': cluster_name,
                           'Tags': kinds,
                           'Address': address,
                           'Port': port,
                           'Check': {
                               'DeregisterCriticalServiceAfter': deregister_critical,
                               'TTL': service_ttl}
                           }, cls=DateTimeEncoder)

        url = self._base_url + '/agent/service/register'
        async with self._client.put(url, data=data) as resp:
            if resp.status != 200:
                raise Exception()

    async def deregister(self, service_id: str) -> None:
        url = self._base_url + '/agent/service/deregister/' + service_id
        async with self._client.put(url) as resp:
            if resp.status != 200:
                raise Exception()

    async def pass_ttl(self, check_id: str) -> None:
        url = self._base_url + '/agent/check/pass/' + check_id
        async with self._client.put(url) as resp:
            if resp.status != 200:
                raise Exception()


class KeyValueEndpoint:
    def __init__(self, client: aiohttp.ClientSession, url: str):
        self._client = client
        self._base_url = url

    async def create_or_update(self, key: str, value: bytes) -> None:
        url = self._base_url + '/kv/' + key
        async with self._client.put(url, data=value) as resp:
            if resp.status != 200:
                raise Exception()

    async def read(self, key: str, recurse=True) -> dict:
        params = None
        if recurse:
            params = {'recurse': ''}
        url = self._base_url + '/kv/' + key
        async with self._client.get(url, params=params) as resp:
            if resp.status != 200:
                raise Exception()
            return await resp.json()

    async def delete(self, key: str) -> None:
        url = self._base_url + '/kv/' + key
        async with self._client.delete(url) as resp:
            if resp.status != 200:
                raise Exception()


class HealthEndpoint():
    def __init__(self, client: aiohttp.ClientSession, url: str):
        self._client = client
        self._base_url = url

    async def service(self, cluster_name: str, index: int, blocking_wait_time: timedelta) -> QueryResult:
        url = f'{self._base_url}/health/checks/{cluster_name}'
        params = {'index': index,
                  'wait': self.__convert_time(blocking_wait_time)}

        async with self._client.get(url, params=params) as resp:
            if resp.status != 200:
                raise Exception()
            statuses = []
            for response in await resp.json():
                service_id = response['ServiceID']
                address = service_id[(service_id.find('@') + 1):(service_id.find(':'))]
                port = service_id[(service_id.find(':') + 1):]
                tags = response['ServiceTags']
                statuses.append(ServiceEntry(address, port, tags))
            return QueryResult(int(resp.headers['X-Consul-Index']), statuses)

    def __convert_time(self, time: timedelta):
        if time.total_seconds() < 60:
            return str(int(time.total_seconds())) + 's'
        else:
            return str(time.total_seconds() / 60) + 'm'


class ConsulClient():
    def __init__(self):
        self._client = None
        self._base_url = None
        self._service_endpoint = None
        self._key_value_endpoint = None
        self._health_endpoint = None

    @property
    def service(self) -> ServiceEndpoint:
        return self._service_endpoint

    @property
    def key_value_storage(self) -> KeyValueEndpoint:
        return self._key_value_endpoint

    @property
    def health(self) -> HealthEndpoint:
        return self._health_endpoint

    @classmethod
    async def create(cls, config: ConsulClientConfiguration) -> 'ConsulClient':
        self = cls()
        self._base_url = f'{config.address}/v1/'
        self._client = aiohttp.ClientSession()
        self._service_endpoint = ServiceEndpoint(self._client, self._base_url)
        self._key_value_endpoint = KeyValueEndpoint(self._client, self._base_url)
        self._health_endpoint = HealthEndpoint(self._client, self._base_url)
        return self

    async def close(self):
        await self._client.close()
