from protoactor.actor import PID


class WatchPidRequest():
    def __init__(self, pid: PID):
        self.pid = pid