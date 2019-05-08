from protoactor.actor.protos_pb2 import PID


class ProcessNameExistException(Exception):
    def __init__(self, name: str, pid: PID):
        super().__init__('a Process with the name %s already exists' % name)
        self.name = name
        self.pid = pid