import asyncio

from examples.remote_benchmark.messages.protos_pb2 import DESCRIPTOR, StartRemote, Ping, Start, Pong
from protoactor.actor import PID
from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import RootContext, AbstractContext
from protoactor.actor.props import Props
from protoactor.remote.remote import Remote
from protoactor.remote.serialization import Serialization


class EchoActor(Actor):
    def __init__(self):
        self._sender: PID = None

    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, StartRemote):
            self._sender = message.Sender
            await context.respond(Start())
        elif isinstance(message, Ping):
            await context.send(self._sender, Pong())


async def main():
    context = RootContext()
    Serialization().register_file_descriptor(DESCRIPTOR)
    Remote().start("192.168.1.77", 12000)
    context.spawn_named(Props.from_producer(lambda: EchoActor()), 'remote')
    input()


if __name__ == "__main__":
    asyncio.run(main())
