import asyncio
import sys

from examples.cluster_grain_hello_world.messages.protos import AbstractHelloGrain, Grains
from examples.cluster_grain_hello_world.messages.protos_pb2 import DESCRIPTOR, HelloRequest, HelloResponse
from protoactor.remote.serialization import Serialization
from protoactor.cluster.providers.consul.consul_client import ConsulClientConfiguration
from protoactor.cluster.providers.consul.consul_provider import ConsulProvider
from protoactor.cluster.сluster import Cluster


class HelloGrain(AbstractHelloGrain):
    async def say_hello(self, request: HelloRequest) -> HelloResponse:
        return HelloResponse(message='Hello from typed grain')


async def start(argv):
    Serialization().register_file_descriptor(DESCRIPTOR)

    Grains.hello_grain_factory(HelloGrain())

    await Cluster.start('MyCluster', '192.168.1.129', 12000,
                        ConsulProvider(ConsulClientConfiguration(f'http://192.168.1.35:8500/')))


    await asyncio.sleep(10000)
    input()
    print('Shutting Down...')
    await Cluster.shutdown()


def main(argv):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start(argv))
    loop.close()


if __name__ == "__main__":
    main(sys.argv[1:])
