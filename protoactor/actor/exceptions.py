from protoactor.actor.protos_pb2 import PID


class BaseCancelTokenException(Exception):
    """
    Base exception class for the `asyncio-cancel-token` library.
    """
    pass


class EventLoopMismatch(BaseCancelTokenException):
    """
    Raised when two different asyncio event loops are referenced, but must be equal
    """
    pass


class OperationCancelled(BaseCancelTokenException):
    """
    Raised when an operation was cancelled.
    """
    pass


class ProcessNameExistException(Exception):
    def __init__(self, name: str, pid: PID):
        super().__init__('a Process with the name %s already exists' % name)
        self.name = name
        self.pid = pid
