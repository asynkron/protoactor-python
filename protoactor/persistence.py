from .actor import Actor
from abc import ABCMeta, abstractmethod
from typing import List, Callable, Tuple, Any
import asyncio 

class Persistent():
    def __init__(self):
        self.state = None
        self.event_index = None
        self.context = None
        self.recovering = None
    
    @property
    def name(self):
        return self.context.self.id

    # @asyncio.coroutine
    # def init(self, provider, context):
    #     self.state = provider.get_state()
    #     self.context = context
    #     self.recovering = true
    #     state.restart()

    #     snapshot = yield from state.get_snapshot()
    #     if snapshot is not None:
    #         self.event_index = snapshot.[1]
    #         #context.receive(snapshot[0])

    #     def 
        
    #     yield from state.get_events(self.name, )


class PersistentActor (Actor):
    @abstractmethod
    def persistence () -> 'Persistance':
        raise NotImplementedError('Should implement this method')

class Provider (metaclass=ABCMeta):
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

class InMemoryProviderState (ProviderState):
    def __init__(self) -> None:
        self.__events = {}
        self.__snapshots = {}

    def restart (self) -> None:
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
