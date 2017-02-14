import threading
from pid import PID
from process import DeadLettersProcess

no_host = "nonhost"


class ProcessRegistry:
    def __init__(self, resolver):
        self._hostResolvers = [resolver]
        # python dict structure is atomic for primitive actions. Need to be checked
        self.__local_actor_refs = {}
        self.__sequence_id = 0
        self.__address = no_host
        self.__lock = threading.Lock()

    def __set_addr(self, value):
        self.__address = value
    
    def __get_addr(self):
        return self.__address

    address = property(__get_addr, __set_addr)

    def get(self, pid):
        if pid.address not in [no_host, self.__address]:
            for resolver in self._hostResolvers:
                reff = resolver(pid)
                if reff is None:
                    continue
                
                pid.ref = reff
                return reff

        aref = self.__local_actor_refs.get(pid.id, None)
        if aref is not None:
            return aref

        return DeadLettersProcess()

    def add(self, id, aref):
        pid = PID (id=id, ref=aref, address=self.address)
        self.__local_actor_refs[id] = aref
        return pid

    def remove(self, pid):
        self.__local_actor_refs.pop(pid.id)

    def next_id(self):
        with self.__lock:
            self.__sequence_id += 1
        return self.__sequence_id
