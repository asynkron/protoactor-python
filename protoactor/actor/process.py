import asyncio
from abc import abstractmethod
from multiprocessing import RLock
from typing import Callable, List

from protoactor.actor.cancel_token import CancelToken
from protoactor.actor.event_stream import GlobalEventStream
from protoactor.actor.exceptions import ProcessNameExistException
from protoactor.actor.message_envelope import MessageEnvelope
from protoactor.actor.messages import DeadLetterEvent, Failure, Restart, ResumeMailbox
from protoactor.actor.protos_pb2 import PID, Stop
from protoactor.actor.supervision import AbstractSupervisorStrategy, AbstractSupervisor
from protoactor.actor.utils import Singleton

is_import = False
if is_import:
    from protoactor.mailbox.mailbox import AbstractMailbox


class AbstractProcess:
    @abstractmethod
    async def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None) -> None:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    async def send_system_message(self, pid: 'PID', message: object) -> None:
        raise NotImplementedError('Should implement this method')

    async def stop(self, pid: 'PID') -> None:
        await self.send_system_message(pid, Stop())


class ActorProcess(AbstractProcess):
    def __init__(self, mailbox: 'AbstractMailbox') -> None:
        self._mailbox = mailbox
        self._is_dead = False

    @property
    def mailbox(self) -> 'AbstractMailbox':
        return self._mailbox

    def setis_dead(self, value):
        self._is_dead = value

    def getis_dead(self):
        return self._is_dead

    is_dead = property(getis_dead, setis_dead)

    async def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        self._mailbox.post_user_message(message)

    async def send_system_message(self, pid: 'PID', message: object):
        self._mailbox.post_system_message(message)

    async def stop(self, pid: 'PID') -> None:
        await super(ActorProcess, self).stop(pid)
        self.is_dead = True


class FutureProcess(AbstractProcess):
    def __init__(self, cancellation_token: CancelToken = None) -> None:
        name = ProcessRegistry().next_id()
        self._pid, absent = ProcessRegistry().try_add(name, self)
        if not absent:
            raise ProcessNameExistException(name, self._pid)
        self._loop = asyncio.get_event_loop()
        self._future = self._loop.create_future()
        self._cancellation_token = cancellation_token

    @property
    def pid(self) -> 'PID':
        return self._pid

    @property
    def task(self) -> asyncio.Future:
        return self._future

    async def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None) -> None:
        msg = MessageEnvelope.unwrap_message(message)
        if self._cancellation_token is not None and self._cancellation_token.triggered:
            await self.stop(self.pid)
        else:
            await self.__set_result(msg, self._loop)
            await self.stop(self.pid)

    async def send_system_message(self, pid: 'PID', message: object) -> None:
        if isinstance(message, Stop):
            ProcessRegistry().remove(pid)
        else:
            if self._cancellation_token is None or not self._cancellation_token.triggered:
                await self.__set_result(None, self._loop)
            await self.stop(pid)

    async def __upgrade_state(self, msg):
        self._future.set_result(msg)

    async def __set_result(self, message, loop):
        concurrent = asyncio.run_coroutine_threadsafe(self.__upgrade_state(message), loop=loop)
        return asyncio.wrap_future(concurrent)


class DeadLettersProcess(AbstractProcess, metaclass=Singleton):
    async def send_system_message(self, pid: 'PID', message: object):
        await GlobalEventStream.publish(DeadLetterEvent(pid, message, None))

    async def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        await GlobalEventStream.publish(DeadLetterEvent(pid, message, sender))


class GuardianProcess(AbstractProcess, AbstractSupervisor):
    def __init__(self, strategy: AbstractSupervisorStrategy):
        self._supervisor_strategy = strategy
        self._name = "Guardian%s" % ProcessRegistry().next_id()
        self._pid, absent = ProcessRegistry().try_add(self._name, self)
        if not absent:
            raise ProcessNameExistException(self._name, self._pid)

    async def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None) -> None:
        raise ValueError('Guardian actor cannot receive any user messages.')

    async def send_system_message(self, pid: 'PID', message: object) -> None:
        if isinstance(message, Failure):
            self._supervisor_strategy.handle_failure(self, message.who, message.restart_statistics, message.reason)

    def escalate_failure(self, who: 'PID', reason: Exception) -> None:
        raise ValueError('Guardian cannot escalate failure.')

    async def restart_children(self, reason: Exception, *pids: List['PID']) -> None:
        for pid in pids:
            await pid.send_system_message(Restart(reason))

    async def stop_children(self, *pids: List['PID']) -> None:
        for pid in pids:
            await pid.stop()

    async def resume_children(self, *pids: List['PID']) -> None:
        for pid in pids:
            await pid.send_system_message(ResumeMailbox())

    def children(self) -> List['PID']:
        raise TypeError('Guardian does not hold its children PIDs.')


class ProcessRegistry(metaclass=Singleton):
    def __init__(self) -> None:
        self._hostResolvers = []
        # python dict structure is atomic for primitive actions. Need to be checked
        self._local_actor_refs = {}
        self._sequence_id = 0
        self._address = "nonhost"
        self._lock = RLock()

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, address: str):
        self._address = address

    def register_host_resolver(self, resolver: Callable[['PID'], AbstractProcess]) -> None:
        self._hostResolvers.append(resolver)

    def get(self, pid: 'PID') -> AbstractProcess:
        if pid.address != "nonhost" and pid.address != self._address:
            for resolver in self._hostResolvers:
                reff = resolver(pid)
                if reff is None:
                    continue
                return reff

        ref = self._local_actor_refs.get(pid.id, None)
        if ref is not None:
            return ref

        return DeadLettersProcess()

    def try_add(self, id: str, ref: AbstractProcess) -> 'PID':
        pid = PID(address=self.address, id=id)
        if id not in self._local_actor_refs:
            self._local_actor_refs[id] = ref
            return pid, True

        return pid, False

    def remove(self, pid: 'PID') -> None:
        del self._local_actor_refs[pid.id]



    def next_id(self) -> str:
        with self._lock:
            self._sequence_id += 1

        return str(self._sequence_id)


class Guardians(metaclass=Singleton):
    def __init__(self):
        self.__guardian_strategies = {}

    def get_guardian_pid(self, strategy: AbstractSupervisorStrategy) -> 'PID':
        guardian = self.__guardian_strategies.get(strategy)
        if guardian is None:
            guardian = GuardianProcess(strategy)
            self.__guardian_strategies[strategy] = guardian
        return guardian
