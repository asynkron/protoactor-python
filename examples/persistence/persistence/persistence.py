import asyncio
from random import Random, randint

from examples.persistence.messages.protos_pb2 import RenameCommand, State, RenameEvent
from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import AbstractContext, RootContext
from protoactor.actor.messages import Started
from protoactor.actor.props import Props
from protoactor.persistence.messages import ReplayEvent, PersistedEvent, RecoverSnapshot, RecoverEvent, Snapshot, Event
from protoactor.persistence.persistence import Persistence
from protoactor.persistence.providers.abstract_provider import AbstractProvider
from protoactor.persistence.providers.in_memory_provider import InMemoryProvider
from protoactor.persistence.snapshot_strategies.interval_strategy import IntervalStrategy


class StartLoopActor:
    pass


class LoopParentMessage:
    pass


class LoopActor(Actor):
    def __init__(self):
        pass

    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, Started):
            print('LoopActor - Started')
            await context.send(context.my_self, LoopParentMessage())
        elif isinstance(message, LoopParentMessage):
            async def fn():
                await context.send(context.parent, RenameCommand(name=self.generate_pronounceable_name(5)))
                await asyncio.sleep(0.5)
                await context.send(context.my_self, LoopParentMessage())

            asyncio.create_task(fn())

    @staticmethod
    def generate_pronounceable_name(length: int) -> str:
        name = ''
        vowels = 'aeiou'
        consonants = 'bcdfghjklmnpqrstvwxyz'

        if length % 2 != 0:
            length += 1

        for i in range((length // 2)):
            name = f'{name}{vowels[randint(0, len(vowels) - 1)]}{consonants[randint(0, len(consonants) - 1)]}'

        return name


class MyPersistenceActor(Actor):
    def __init__(self, provider: AbstractProvider):
        self._state = State()
        self._loop_actor = None
        self._timer_started = False
        self._persistence = Persistence.with_event_sourcing_and_snapshotting(provider,
                                                                             provider,
                                                                             'demo-app-id',
                                                                             self.__apply_event,
                                                                             self.__apply_snapshot,
                                                                             IntervalStrategy(20),
                                                                             lambda: self._state)

    def __apply_event(self, event: Event) -> None:
        if isinstance(event, RecoverEvent):
            if isinstance(event.data, RenameEvent):
                self._state.name = event.name
                print(f'MyPersistenceActor - RecoverEvent = Event.Index = {event.index}, Event.Data = {event.data}')
        elif isinstance(event, ReplayEvent):
            if isinstance(event.data, RenameEvent):
                self._state.name = event.name
                print(f'MyPersistenceActor - ReplayEvent = Event.Index = {event.index}, Event.Data = {event.data}')
        elif isinstance(event, PersistedEvent):
            print(f'MyPersistenceActor - PersistedEvent = Event.Index = {event.index}, Event.Data = {event.data}')

    def __apply_snapshot(self, snapshot: Snapshot) -> None:
        if isinstance(snapshot, RecoverSnapshot):
            if isinstance(snapshot.state, State):
                self._state = snapshot.state
                print(f'MyPersistenceActor - RecoverSnapshot = Snapshot.Index = {self._persistence.index}, '
                      f'Snapshot.State = {snapshot.state.name}')

    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, Started):
            print('MyPersistenceActor - Started')
            print(f'MyPersistenceActor - Current State: {self._state}')
            await self._persistence.recover_state()
            await context.send(context.my_self, StartLoopActor())
        elif isinstance(message, StartLoopActor):
            await self.__process_start_loop_actor_message(context, message)
        elif isinstance(message, RenameCommand):
            await self.__process_rename_command_message(message)

    async def __process_start_loop_actor_message(self, context, message):
        if self._timer_started:
            return
        self._timer_started = True
        print('MyPersistenceActor - StartLoopActor')
        props = Props.from_producer(lambda: LoopActor())
        self._loop_actor = context.spawn(props)

    async def __process_rename_command_message(self, message):
        print('MyPersistenceActor - RenameCommand')
        self._state.Name = message.name
        await self._persistence.persist_event(RenameEvent(name=message.name))


async def main():
    context = RootContext()
    provider = InMemoryProvider()

    props = Props.from_producer(lambda: MyPersistenceActor(provider))
    pid = context.spawn(props)

    input()


if __name__ == "__main__":
    asyncio.run(main())
