import threading
from pid import PID
from process import DeadLettersProcess

__no_host = "nonhost"

class ProcessRegistry:
    def __init__(resolver):
        self._hostResolvers = [resolver]
        # python dict structure is atomic for primitive actions. Need to be checked
        self._local_actor_refs = {}
        self.sequence_id = 0
        self.address = __no_host
        self._lock = threading.Lock()

    def get(self, pid):
        if pid.address not in [__no_host, self.address]:
            for resolver in self._hostResolvers:
                reff = resolver(pid)
                if reff is None:
                    continue
                
                pid.ref = reff
                return reff

        aref = self._local_actor_refs.get('host', None)
        if aref is not None:
            return aref

        return DeadLettersProcess()

    def add(id, aref):
        pid = PID (id=id, aref=aref, address=self.address)
        self._localActorRefs[id] = aref
        return pid

    def remove(self, pid):
        self._local_actor_refs.pop(pid.id)

    def next_id(self):
        with self._lock:
            self.sequence_id += 1
        return self.sequence_id
