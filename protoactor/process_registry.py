from multiprocessing import RLock

from protoactor.utils import singleton
from . import utils, process
from .protos_pb2 import PID


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

    def register_host_resolver(self, resolver):
        self._hostResolvers.append(resolver)

    def get(self, pid: 'PID') -> process.AbstractProcess:
        if pid.address != "nonhost" and pid.address != self.__address:
            for resolver in self._hostResolvers:
                reff = resolver(pid)
                if reff is None:
                    continue

                return reff

        ref = self.__local_actor_refs.get(pid.id, None)
        if ref is not None:
            return ref

        return process.DeadLettersProcess()

    def add(self, id: str, ref: process.AbstractProcess) -> 'PID':
        # _pid = pid_.PID(address=self.address, id=id, ref=ref)
        pid = PID()
        pid.address = self.address
        pid.id = id
        self.__local_actor_refs[id] = ref
        return pid

    def remove(self, pid: 'PID') -> None:
        self.__local_actor_refs.pop(pid.id)

    def next_id(self) -> str:
        with self.__lock:
            self.__sequence_id += 1

        return str(self.__sequence_id)
