import asyncio
import getopt
import sys
from collections import namedtuple
from datetime import timedelta

from examples.cluster_hello_world.messages.protos_pb2 import DESCRIPTOR, HelloRequest, HelloResponse
from protoactor.actor.actor_context import RootContext, AbstractContext
from protoactor.actor.props import Props
from protoactor.remote.remote import Remote
from protoactor.remote.serialization import Serialization
from protoactor.cluster.providers.consul.consul_client import ConsulClientConfiguration
from protoactor.cluster.providers.consul.consul_provider import ConsulProvider
from protoactor.cluster.providers.single_remote_instance.single_remote_instance_provider import \
    SingleRemoteInstanceProvider
from protoactor.cluster.сluster import Cluster

Node2Config = namedtuple('Node1Config', 'server_name consul_url')


async def start(argv):
    Serialization().register_file_descriptor(DESCRIPTOR)

    async def fn(ctx: AbstractContext):
        if isinstance(ctx.message, HelloRequest):
            await ctx.respond(HelloResponse(message='Hello from node 2'))

    props = Props.from_func(fn)
    parsed_args = parse_args(argv)
    Remote().register_known_kind("HelloKind", props)

    # await Cluster.start('MyCluster', parsed_args.server_name, 12000,
    #                     SingleRemoteInstanceProvider(parsed_args.server_name, 12000))

    await Cluster.start('MyCluster', parsed_args.server_name, 12000,
                        ConsulProvider(ConsulClientConfiguration(f'http://{parsed_args.consul_url}:8500/')))

    await asyncio.sleep(timedelta(days=180).total_seconds())
    print('Shutting Down...')
    await Cluster.shutdown()

def parse_args(argv):
    opts, args = getopt.getopt(argv, ["server name=", "consul url=", "start consul="])
    if len(opts) > 0:
        Node2Config(opts[0][0], opts[1][0])
    return Node2Config('192.168.1.129', '192.168.1.35')

def main(argv):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start(argv))
    loop.close()


if __name__ == "__main__":
    main(sys.argv[1:])
