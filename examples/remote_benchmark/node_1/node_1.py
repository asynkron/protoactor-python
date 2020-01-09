import asyncio
import datetime
import time
from threading import Event

from examples.remote_benchmark.messages.protos_pb2 import Pong, DESCRIPTOR, StartRemote, Ping
from protoactor.actor import PID
from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import AbstractContext, RootContext
from protoactor.actor.props import Props
from protoactor.remote.remote import Remote
from protoactor.remote.serialization import Serialization


class LocalClient(Actor):
    def __init__(self, count: int, message_count: int, wg: Event, loop):
        self._count = count
        self._message_count = message_count
        self._wg = wg
        self._loop = loop

    async def notify(self) -> None:
        self._wg.set()

    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, Pong):
            self._count += 1
            if self._count % 5 == 0:
                print(self._count)
            if self._count == self._message_count:
                asyncio.run_coroutine_threadsafe(self.notify(), self._loop)



async def main():
    context = RootContext()
    Serialization().register_file_descriptor(DESCRIPTOR)
    Remote().start("192.168.1.129", 12001)

    wg = asyncio.Event()
    message_count = 10000

    props = Props.from_producer(lambda: LocalClient(0, message_count, wg, asyncio.get_event_loop()))

    pid = context.spawn(props)
    remote = PID(address="192.168.1.77:12000", id="remote")

    await context.request_future(remote, StartRemote(Sender=pid))

    start = datetime.datetime.now()
    print('Starting to send')
    for i in range(message_count):
        await context.send(remote, Ping())
    await wg.wait()

    elapsed = datetime.datetime.now() - start
    print(f'Elapsed {elapsed}')

    t = message_count * 2.0 / elapsed.total_seconds()
    print(f'Throughput {t} msg / sec')

    input()


if __name__ == "__main__":
    asyncio.run(main())

