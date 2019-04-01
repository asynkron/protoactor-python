import asyncio
from abc import abstractmethod
from multiprocessing import RLock
from typing import Callable, List

from protoactor.actor import message_sender
from protoactor.actor.cancel_token import CancelToken
from protoactor.actor.event_stream import GlobalEventStream
from protoactor.actor.exceptions import ProcessNameExistException
from protoactor.actor.message_envelope import MessageEnvelope
from protoactor.actor.messages import DeadLetterEvent, Failure, Restart
from protoactor.actor.protos_pb2 import PID, Stop
from protoactor.actor.supervision import AbstractSupervisorStrategy, AbstractSupervisor
from protoactor.actor.utils import singleton
from protoactor.mailbox.messages import ResumeMailbox

is_import = False
if is_import:
    from protoactor.mailbox.mailbox import AbstractMailbox


class AbstractProcess:
    @abstractmethod
    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None) -> None:
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def send_system_message(self, pid: 'PID', message: object) -> None:
        raise NotImplementedError('Should implement this method')

    def stop(self, pid: 'PID') -> None:
        self.send_system_message(pid, Stop())


class LocalProcess(AbstractProcess):
    def __init__(self, mailbox: 'AbstractMailbox') -> None:
        self.__mailbox = mailbox
        self.__is_dead = False

    @property
    def mailbox(self) -> 'AbstractMailbox':
        return self.__mailbox

    def setis_dead(self, value):
        self.__is_dead = value

    def getis_dead(self):
        return self.__is_dead

    is_dead = property(getis_dead, setis_dead)

    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        if sender:
            self.__mailbox.post_user_message(message_sender.MessageSender(message, sender))
        else:
            self.__mailbox.post_user_message(message)

    def send_system_message(self, pid: 'PID', message: object):
        self.__mailbox.post_system_message(message)

    def stop(self, pid: 'PID') -> None:
        super(LocalProcess, self).stop(pid)
        self.is_dead = True


class FutureProcess(AbstractProcess):
    def __init__(self, cancellation_token: CancelToken = None) -> None:
        name = ProcessRegistry().next_id()
        self.__pid, absent = ProcessRegistry().try_add(name, self)
        if not absent:
            raise ProcessNameExistException(name, self.__pid)
        self.__loop = asyncio.get_event_loop()
        self.__future = self.__loop.create_future()
        self.__cancellation_token = cancellation_token

    @property
    def pid(self) -> 'PID':
        return self.__pid

    @property
    def task(self) -> asyncio.Future:
        return self.__future

    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None) -> None:
        msg = MessageEnvelope.unwrap_message(message)
        if self.__cancellation_token is not None and self.__cancellation_token.triggered:
            self.stop(self.pid)
        else:
            self.__loop.call_soon_threadsafe(self.__future.set_result, msg)
            self.stop(self.pid)

    def send_system_message(self, pid: 'PID', message: object) -> None:
        if isinstance(message, Stop):
            ProcessRegistry().remove(pid)
        else:
            if self.__cancellation_token is None or not self.__cancellation_token.triggered:
                self.__future.set_result(None)
            self.stop(pid)

    async def cancellable_wait(self, timeout: float = None) -> None:
        done, pending = await asyncio.wait({self.__future}, timeout=timeout)

        if not done:
            self.__future.cancel()
            self.stop(self.pid)
            raise TimeoutError()


class DeadLettersProcess(AbstractProcess, metaclass=singleton):
    def send_system_message(self, pid: 'PID', message: object):
        GlobalEventStream().instance.publish(DeadLetterEvent(pid, message, None))

    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        GlobalEventStream().instance.publish(DeadLetterEvent(pid, message, sender))


class GuardianProcess(AbstractProcess, AbstractSupervisor):
    def __init__(self, strategy: AbstractSupervisorStrategy):
        self.__supervisor_strategy = strategy
        self.__name = "Guardian%s" % ProcessRegistry().next_id()
        self.__pid, absent = ProcessRegistry().try_add(self.__name, self)
        if not absent:
            raise ProcessNameExistException(self.__name, self.__pid)

    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None) -> None:
        raise ValueError('Guardian actor cannot receive any user messages.')

    def send_system_message(self, pid: 'PID', message: object) -> None:
        if isinstance(message, Failure):
            self.__supervisor_strategy.handle_failure(self, message.who, message.restart_statistics, message.reason)

    def escalate_failure(self, who: 'PID', reason: Exception) -> None:
        raise ValueError('Guardian cannot escalate failure.')

    def restart_children(self, reason: Exception, *pids: List['PID']) -> None:
        for pid in pids:
            pid.send_system_message(Restart(reason))

    def stop_children(self, *pids: List['PID']) -> None:
        for pid in pids:
            pid.stop()

    def resume_children(self, *pids: List['PID']) -> None:
        for pid in pids:
            pid.send_system_message(ResumeMailbox())

    def children(self) -> List['PID']:
        raise TypeError('Guardian does not hold its children PIDs.')


class ProcessRegistry(metaclass=singleton):
    def __init__(self) -> None:
        self._hostResolvers = []
        # python dict structure is atomic for primitive actions. Need to be checked
        self.__local_actor_refs = {}
        self.__sequence_id = 0
        self.__address = "nonhost"
        self.__lock = RLock()

    @property
    def address(self) -> str:
        return self.__address

    @address.setter
    def address(self, address: str):
        self.__address = address

    def register_host_resolver(self, resolver: Callable[['PID'], AbstractProcess]) -> None:
        self._hostResolvers.append(resolver)

    def get(self, pid: 'PID') -> AbstractProcess:
        if pid.address != "nonhost" and pid.address != self.__address:
            for resolver in self._hostResolvers:
                reff = resolver(pid)
                if reff is None:
                    continue
                return reff

        ref = self.__local_actor_refs.get(pid.id, None)
        if ref is not None:
            return ref

        return DeadLettersProcess()

    def try_add(self, id: str, ref: AbstractProcess) -> 'PID':
        pid = PID(address=self.address, id=id)
        if id not in self.__local_actor_refs:
            self.__local_actor_refs[id] = ref
            return pid, True
        else:
            return pid, False

    def remove(self, pid: 'PID') -> None:
        self.__local_actor_refs.pop(pid.id)

    def next_id(self) -> str:
        with self.__lock:
            self.__sequence_id += 1

        return str(self.__sequence_id)


class Guardians(metaclass=singleton):
    def __init__(self):
        self.__guardian_strategies = {}

    def get_guardian_pid(self, strategy: AbstractSupervisorStrategy) -> 'PID':
        guardian = self.__guardian_strategies.get(strategy)
        if guardian is None:
            guardian = GuardianProcess(strategy)
            self.__guardian_strategies[strategy] = guardian
        return guardian
