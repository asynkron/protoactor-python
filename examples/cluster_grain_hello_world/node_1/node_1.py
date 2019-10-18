import asyncio
import sys

from examples.cluster_grain_hello_world.messages.protos import Grains
from examples.cluster_grain_hello_world.messages.protos_pb2 import DESCRIPTOR, HelloRequest
from protoactor.remote.serialization import Serialization
from protoactor.сluster.providers.consul.consul_client import ConsulClientConfiguration
from protoactor.сluster.providers.consul.consul_provider import ConsulProvider
from protoactor.сluster.сluster import Cluster


async def start(argv):
    Serialization().register_file_descriptor(DESCRIPTOR)
    await Cluster.start('MyCluster', '127.0.0.1', 12001,
                        ConsulProvider(ConsulClientConfiguration(f'http://192.168.1.35:8500/')))

    client = Grains.hello_grain("Roger")
    res = await client.say_hello(HelloRequest())
    print(res.message)
    input()

    res = await client.say_hello(HelloRequest())
    print(res.message)
    input()

    print('Shutting Down...')
    await Cluster.shutdown()

def main(argv):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start(argv))
    loop.close()

if __name__ == "__main__":
    main(sys.argv[1:])