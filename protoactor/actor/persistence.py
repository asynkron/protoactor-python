
from abc import ABCMeta, abstractmethod
from typing import Callable, Tuple, Any

from protoactor.actor.actor import Actor


class Persistent():
    def __init__(self):
        self._state = None
        self._index = None
        self._context = None
        self._recovering = None

    @property
    def name(self):
        return self._context.my_self.id

    @property
    def actor_id(self):
        return self._context.self.id

    async def init(self, provider, context, actor):
        self._state = provider.get_state()
        self._context = context
        self._actor = actor

        snapshot, index = await self._state.get_snapshot()
        if snapshot is not None:
            self._index = index
            actor.update_state(RecoverSnapshot(snapshot, self._index))

        def update_actor_state_with_event(e):
            self._index += 1
            actor.update_state(RecoverEvent(e, self._index))

        await self._state.get_events(self.actor_id, index, update_actor_state_with_event)

    async def persist_event_async(self, event):
        self._index += 1
        await self._state.persist_event(self.actor_id, self._index, event)
        self._actor.update_state(PersistedEvent(event, self._index))

    async def persist_snapshot(self, snapshot):
        await self._state.persist_snapshot(self.actor_id, self._index, snapshot)

    async def delete_snapshot(self, inclusive_to_index):
        await self._state.delete_snapshot(inclusive_to_index)

    async def delete_events(self, inclusive_to_index):
        await self._state.delete_event(inclusive_to_index)


class Snapshot():
    def __init__(self, state, index):
        self._state = state
        self._index = index

    @property
    def state(self):
        return self._state

    @property
    def index(self):
        return self._index


class RecoverSnapshot(Snapshot):
    def __init__(self, state, index):
        super(RecoverSnapshot, self).__init__(state, index)


class PersistedSnapshot(Snapshot):
    def __init__(self, state, index):
        super(PersistedSnapshot, self).__init__(state, index)


class Event():
    def __init__(self, data, index):
        self._data = data
        self._index = index

    @property
    def data(self):
        return self._data

    @property
    def index(self):
        return self._index


class RecoverEvent(Event):
    def __init__(self, data, index):
        super(RecoverEvent, self).__init__(data, index)


class PersistedEvent(Event):
    def __init__(self, data, index):
        super(PersistedEvent, self).__init__(data, index)


class Persistance():
    pass


class PersistentActor(Actor):
    @abstractmethod
    def persistence(self) -> 'Persistance':
        raise NotImplementedError('Should implement this method')


class Provider(metaclass=ABCMeta):
    @abstractmethod
    def get_state(self) -> 'ProviderState':
        raise NotImplementedError('Should implement this method')


class ProviderState(metaclass=ABCMeta):
    @abstractmethod
    async def get_events(self, actor_name: str, index_start: int, callback: Callable[..., None]) -> None:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    async def get_snapshot(self, actor_name: str) -> Tuple[Any, int]:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    async def persist_event(self, actor_name: str, index: int, event: Any) -> None:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    async def persist_snapshot(self, actor_name: str, index: int, snapshot: Any) -> None:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    async def delete_events(self, actor_name: str, inclusive_to_index: int, event: Any) -> None:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    async def delete_snapshots(self, actor_name: str, inclusive_to_index: int, snapshot: Any) -> None:
        raise NotImplementedError('Should implement this method')


class InMemoryProvider(Provider):
    def get_state(self) -> ProviderState:
        return InMemoryProviderState()


class InMemoryProviderState(ProviderState):
    def __init__(self) -> None:
        self._events = {}
        self._snapshots = {}

    def get_snapshot_interval(self) -> int:
        return 0

    async def get_snapshot(self, actor_name: str) -> Tuple[Any, int]:
        snapshot = self._snapshots.get(actor_name, None)
        return snapshot

    async def get_events(self, actor_name: str, event_index_start: int, callback: Callable[..., None]) -> None:
        events = self._events.get(actor_name, None)
        if events is not None:
            for e in events:
                callback(e)

    async def persist_event(self, actor_name: str, event_index: int, event: Any) -> None:
        events = self._events.setdefault(actor_name, [])
        events.append(event)

    async def persist_snapshot(self, actor_name: str, event_index: int, snapshot: Any) -> None:
        self._snapshots[actor_name] = snapshot, event_index

    async def delete_events(self, actor_name: str, inclusive_to_index: int, event: Any) -> None:
        self._events.pop(actor_name)

    async def delete_snapshots(self, actor_name: str, inclusive_to_index: int, snapshot: Any) -> None:
        self._snapshots.pop(actor_name)
