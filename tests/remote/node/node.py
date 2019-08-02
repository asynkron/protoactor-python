import asyncio
import getopt
import multiprocessing
import sys
from time import sleep

from protoactor.actor.actor import Actor, RootContext
from protoactor.actor.messages import Started
from protoactor.actor.props import Props
from protoactor.remote.remote import Remote
from protoactor.remote.serialization import Serialization
from tests.remote.messages.protos_pb2 import Ping, Pong
from tests.remote.messages.protos_pb2 import DESCRIPTOR


class EchoActor(Actor):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    async def receive(self, context):
        if isinstance(context.message, Ping):
            await context.respond(Pong(message="%s:%s %s" % (self._host, self._port, context.message.message)))

async def start(argv):
    host = None
    port = None
    opts, args = getopt.getopt(argv, "hp", ["host=", "port="])
    for opt, arg in opts:
        if opt == '--host':
            host = arg
        elif opt == '--port':
            port = arg

    Serialization().register_file_descriptor(DESCRIPTOR)

    context = RootContext()
    Remote().start(host, port)
    props = Props().from_producer(lambda: EchoActor(host, port))
    Remote().register_known_kind('EchoActor', props)
    context.spawn_named(props, "EchoActorInstance")

    input()


def main(argv):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start(argv))
    loop.close()


if __name__ == "__main__":
    main(sys.argv[1:])
