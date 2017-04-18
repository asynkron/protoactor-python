from .actor import Actor
from abc import ABCMeta, abstractmethod
from typing import Callable, Tuple, Any


class Persistent():
    def __init__(self):
        self.__state = None
        self.__index = None
        self.__context = None
        self.__recovering = None

    @property
    def name(self):
        return self.__context.my_self.id

    @property
    def actor_id(self):
        return self.__context.self.id

    async def init(self, provider, context, actor):
        self.__state = provider.get_state()
        self.__context = context
        self.__actor = actor

        snapshot, index = await self.__state.get_snapshot()
        if snapshot is not None:
            self.__index = index
            actor.update_state(RecoverSnapshot(snapshot, ))

        def update_actor_state_with_event(e):
            self.__index += 1
            actor.update_state(RecoverEvent(e, self.__index))

        await self.__state.get_events(self.actor_id, index, update_actor_state_with_event)

    async def persist_event_async(self, event):
        self.__index += 1
        await self.__state.persist_event(self.actor_id, self.__index, event)
        self.__actor.update_state(PersistedEvent(event, self.__index))

    async def persist_snapshot(self, snapshot):
        await self.__state.persist_snapshot(self.actor_id, self.__index, snapshot)

    async def delete_snapshot(self, inclusive_to_index):
        await self.__state.delete_snapshot(inclusive_to_index)

    async def delete_events(self, inclusive_to_index):
        await self.__state.delete_event(inclusive_to_index)


class Snapshot():
    def __init__(self, state, index):
        self.__state = state
        self.__index = index

    @property
    def state(self):
        return self.__state

    @property
    def index(self):
        return self.__index


class RecoverSnapshot(Snapshot):
    def __init__(self, state, index):
        super(RecoverSnapshot, self).__init__(state, index)

class PersistedSnapshot(Snapshot):
    def __init__(self, state, index):
        super(PersistedSnapshot, self).__init__(state, index)


class Event():
    def __init__(self, data, index):
        self.__data = data
        self.__index = index

    @property
    def data(self):
        return self.__data

    @property
    def index(self):
        return self.__index


class RecoverEvent(Event):
    def __init__(self, data, index):
        super(RecoverEvent, self).__init__(data, index)

class PersistedEvent(Event):
    def __init__(self, data, index):
        super(PersistedEvent, self).__init__(data, index)


class PersistentActor(Actor):
    @abstractmethod
    def persistence() -> 'Persistance':
        raise NotImplementedError('Should implement this method')


class Provider(metaclass=ABCMeta):
    @abstractmethod
    def get_state() -> 'ProviderState':
        raise NotImplementedError('Should implement this method')

class ProviderState(metaclass=ABCMeta):
    @abstractmethod
    async def get_events(self, actor_name: str, event_index_start: int, callback: Callable[..., None]) -> None:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    async def get_snapshot(self, actor_name: str) -> Tuple[Any, int]:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def get_snapshot_interval(self) -> int:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    async def persist_event(self, actor_name: str, event_index: int, event: Any) -> None:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    async def persist_snapshot(self, actor_name: str, event_index: int, snapshot: Any) -> None:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def restart(self) -> None:
        raise NotImplementedError('Should implement this method')


class InMemoryProvider(Provider):
    def get_state(self) -> ProviderState:
        return InMemoryProviderState()


class InMemoryProviderState(ProviderState):
    def __init__(self) -> None:
        self.__events = {}
        self.__snapshots = {}

    def restart(self) -> None:
        pass

    def get_snapshot_interval(self) -> int:
        return 0

    async def get_snapshot(self, actor_name: str) -> Tuple[Any, int]:
        snapshot = self.__snapshots.get(actor_name, None)
        return snapshot

    async def get_events(self, actor_name: str, event_index_start: int, callback: Callable[..., None]) -> None:
        events = self.__events.get(actor_name, None)
        if events is not None:
            for e in events:
                callback(e)

    async def persist_event(self, actor_name: str, event_index: int, event: Any) -> None:
        events = self.__events.setdefault(actor_name, [])
        events.append(event)

    async def persist_snapshot(self, actor_name: str, event_index: int, snapshot: Any) -> None:
        self.__snapshots[actor_name] = snapshot, event_index
