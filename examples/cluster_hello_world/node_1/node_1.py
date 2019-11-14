import asyncio
import getopt
import sys
from collections import namedtuple
from datetime import timedelta

from examples.cluster_hello_world.messages.protos_pb2 import DESCRIPTOR, HelloRequest
from protoactor.actor.actor_context import RootContext
from protoactor.remote.response import ResponseStatusCode
from protoactor.remote.serialization import Serialization
from protoactor.cluster.providers.consul.consul_client import ConsulClientConfiguration
from protoactor.cluster.providers.consul.consul_provider import ConsulProvider
from protoactor.cluster.providers.single_remote_instance.single_remote_instance_provider import \
    SingleRemoteInstanceProvider
from protoactor.cluster.сluster import Cluster

Node1Config = namedtuple('Node1Config', 'server_name consul_url start_consul')


async def start(argv):
    context = RootContext()
    Serialization().register_file_descriptor(DESCRIPTOR)
    parsed_args = parse_args(argv)

    # await Cluster.start('MyCluster', parsed_args.server_name, 12002, SingleRemoteInstanceProvider('192.168.1.72', 12000))

    await Cluster.start('MyCluster', parsed_args.server_name, 12001,
                        ConsulProvider(ConsulClientConfiguration(f'http://{parsed_args.consul_url}:8500/')))

    pid, sc = await Cluster.get_async("TheName", "HelloKind")
    while sc != ResponseStatusCode.OK:
        await asyncio.sleep(0.5)
        pid, sc = await Cluster.get_async("TheName", "HelloKind")

    res = await context.request_future(pid, HelloRequest())
    print(res.message)
    await asyncio.sleep(timedelta(days=180).total_seconds())
    print('Shutting Down...')
    await Cluster.shutdown()

def parse_args(argv):
    opts, args = getopt.getopt(argv, ["server name=", "consul url=", "start consul="])
    if len(opts) > 0:
        Node1Config(opts[0][0], opts[1][0], True)
    return Node1Config('192.168.1.35', '127.0.0.1', True)


def main(argv):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start(argv))
    loop.close()


if __name__ == "__main__":
    main(sys.argv[1:])
