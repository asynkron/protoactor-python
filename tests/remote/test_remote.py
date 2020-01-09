import asyncio
import uuid
from datetime import timedelta

import pytest

from protoactor.actor import PID
from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import RootContext, AbstractContext
from protoactor.actor.messages import Started
from protoactor.actor.props import Props
from protoactor.actor.protos_pb2 import Unwatch, Terminated
from protoactor.remote.remote import Remote
from tests.remote.messages.protos_pb2 import Ping
from tests.remote.remote_manager import RemoteManager

root_context = RootContext()

@pytest.fixture(scope="session")
def remote_manager():
    return RemoteManager()


@pytest.mark.asyncio
async def test_can_spawn_remote_actor(remote_manager):
    remote_actor_name = str(uuid.uuid4())
    remote_actor_resp = await Remote().spawn_named_async(remote_manager.default_node_address,
                                                         remote_actor_name,
                                                         'EchoActor', timedelta(seconds=5))
    remote_actor = remote_actor_resp.pid
    pong = await root_context.request_future(remote_actor, Ping(message='Hello'), timeout=timedelta(seconds=5))
    assert "%s Hello" % remote_manager.default_node_address == pong.message


@pytest.mark.asyncio
async def test_can_send_and_receive_to_existing_remote(remote_manager):
    remote_actor = PID(address=remote_manager.default_node_address, id='EchoActorInstance')
    pong = await root_context.request_future(remote_actor, Ping(message="Hello"), timeout=timedelta(seconds=0.5))
    assert "%s Hello" % remote_manager.default_node_address == pong.message


@pytest.mark.asyncio
async def test_when_remote_actor_not_found_request_async_timesout(remote_manager):
    unknown_remote_actor = PID(address=remote_manager.default_node_address, id="doesn't exist")
    with pytest.raises(TimeoutError) as e:
        await root_context.request_future(unknown_remote_actor, Ping(message='Hello'), timeout=timedelta(seconds=0.2))

    assert 'TimeoutError' in str(e)


@pytest.mark.asyncio
async def test_can_watch_remote_actor(remote_manager):
    remote_actor = await spawn_remote_actor(remote_manager.default_node_address)
    local_actor = await spawn_local_actor_and_watch([remote_actor])
    await remote_actor.stop()

    async def func():
        return await root_context.request_future(local_actor,
                                                 TerminatedMessageReceived(remote_manager.default_node_address,
                                                                          remote_actor.id),
                                                 timeout=timedelta(seconds=5))

    assert await poll_until_true(func)


@pytest.mark.asyncio
async def test_can_watch_multiple_remote_actors(remote_manager):
    remote_actor1 = await spawn_remote_actor(remote_manager.default_node_address)
    remote_actor2 = await spawn_remote_actor(remote_manager.default_node_address)
    local_actor = await spawn_local_actor_and_watch([remote_actor1, remote_actor2])

    await remote_actor1.stop()
    await remote_actor2.stop()

    async def func1():
        return await root_context.request_future(local_actor,
                                                 TerminatedMessageReceived(remote_manager.default_node_address,
                                                                          remote_actor1.id),
                                                 timeout=timedelta(seconds=5))

    async def func2():
        return await root_context.request_future(local_actor,
                                                 TerminatedMessageReceived(remote_manager.default_node_address,
                                                                          remote_actor2.id),
                                                 timeout=timedelta(seconds=5))

    assert await poll_until_true(func1)
    assert await poll_until_true(func2)


@pytest.mark.asyncio
async def test_multiple_local_actors_can_watch_remote_actor(remote_manager):
    remote_actor = await spawn_remote_actor(remote_manager.default_node_address)

    local_actor1 = await spawn_local_actor_and_watch([remote_actor])
    local_actor2 = await spawn_local_actor_and_watch([remote_actor])

    await remote_actor.stop()

    async def func1():
        return await root_context.request_future(local_actor1,
                                                 TerminatedMessageReceived(remote_manager.default_node_address,
                                                                          remote_actor.id),
                                                 timeout=timedelta(seconds=5))

    async def func2():
        return await root_context.request_future(local_actor2,
                                                 TerminatedMessageReceived(remote_manager.default_node_address,
                                                                          remote_actor.id),
                                                 timeout=timedelta(seconds=5))

    assert await poll_until_true(func1)
    assert await poll_until_true(func2)


@pytest.mark.asyncio
async def test_can_unwatch_remote_actor(remote_manager):
    remote_actor = await spawn_remote_actor(remote_manager.default_node_address)

    local_actor1 = await spawn_local_actor_and_watch([remote_actor])
    local_actor2 = await spawn_local_actor_and_watch([remote_actor])

    await root_context.send(local_actor2, Unwatch(watcher=remote_actor))
    await asyncio.sleep(3)
    await remote_actor.stop()

    async def func1():
        return await root_context.request_future(local_actor1,
                                                 TerminatedMessageReceived(remote_manager.default_node_address,
                                                                          remote_actor.id),
                                                 timeout=timedelta(seconds=5))

    async def func2():
        return await root_context.request_future(local_actor2,
                                                 TerminatedMessageReceived(remote_manager.default_node_address,
                                                                          remote_actor.id),
                                                 timeout=timedelta(seconds=5))

    assert await poll_until_true(func1)
    assert not await poll_until_true(func2)


@pytest.mark.asyncio
async def test_when_remote_terminated_local_watcher_receives_notification(remote_manager):
    address, process = remote_manager.provision_node("127.0.0.1", 12002)

    remote_actor = await spawn_remote_actor(address)
    local_actor = await spawn_local_actor_and_watch([remote_actor])

    process.kill()
    process.wait()

    await root_context.send(local_actor, SendMessageToRemoteActor(remote_actor))
    await asyncio.sleep(1)

    async def func1():
        return await root_context.request_future(local_actor,
                                                 TerminatedMessageReceived(address, remote_actor.id),
                                                 timeout=timedelta(seconds=5))

    assert await poll_until_true(func1)
    assert await root_context.request_future(local_actor, GetTerminatedMessagesCount(),
                                             timeout=timedelta(seconds=5)) == 1


@pytest.fixture(scope="session", autouse=True)
def cleanup(remote_manager):
    yield
    remote_manager.dispose()


async def poll_until_true(predicate, attempts=10, interval=0.005):
    attempt = 1
    while attempt <= attempts:
        if await predicate():
            return True
        attempt += 1
        await asyncio.sleep(interval)

    return False


async def spawn_remote_actor(address):
    remote_actor_name = str(uuid.uuid4())
    remote_actor_resp = await Remote().spawn_named_async(address,
                                                         remote_actor_name,
                                                         'EchoActor', timeout=timedelta(seconds=5))
    return remote_actor_resp.pid


async def spawn_local_actor_and_watch(remote_actors):
    props = Props.from_producer(lambda: LocalActor(remote_actors))
    actor = root_context.spawn(props)
    await asyncio.sleep(2)
    return actor


class TerminatedMessageReceived():
    def __init__(self, address, actor_id):
        self.address = address
        self.actor_id = actor_id


class SendMessageToRemoteActor():
    def __init__(self, actor):
        self.actor = actor


class GetTerminatedMessagesCount:
    pass


class LocalActor(Actor):
    def __init__(self, remote_actors):
        self._remote_actors = remote_actors
        self._terminated_messages = []

    async def receive(self, context: AbstractContext) -> None:
        if isinstance(context.message, Started):
            await self.handle_started(context)
        elif isinstance(context.message, Unwatch):
            await self.handle_unwatch(context)
        elif isinstance(context.message, TerminatedMessageReceived):
            await self.handle_terminated_message_received(context)
        elif isinstance(context.message, GetTerminatedMessagesCount):
            await self.handle_count_of_messages_received(context)
        elif isinstance(context.message, Terminated):
            await self.handle_terminated(context)
        elif isinstance(context.message, SendMessageToRemoteActor):
            await self.handle_send_message_to_remote_actor(context)

    async def handle_started(self, context):
        for remote_actor in self._remote_actors:
            await context.watch(remote_actor)

    async def handle_unwatch(self, context):
        remote_actor = None
        message = context.message
        for rm in self._remote_actors:
            if rm.address == message.watcher.address and rm.id == message.watcher.id:
                remote_actor = rm

        await context.unwatch(remote_actor)

    async def handle_terminated_message_received(self, context):
        message_received = False
        for tm in self._terminated_messages:
            if tm.who.address == context.message.address and tm.who.id == context.message.actor_id:
                message_received = True

        await context.respond(message_received)

    async def handle_count_of_messages_received(self, context):
        await context.respond(len(self._terminated_messages))

    async def handle_terminated(self, context):
        self._terminated_messages.append(context.message)

    async def handle_send_message_to_remote_actor(self, context):
        await context.send(context.message.actor, Ping(message="Hello"))
