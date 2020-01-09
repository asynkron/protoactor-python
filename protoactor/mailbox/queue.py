from abc import abstractmethod, ABCMeta
import queue
from typing import Optional


class AbstractQueue(metaclass=ABCMeta):
    @abstractmethod
    def has_messages(self) -> bool:
        raise NotImplementedError("Should Implement this method.")

    @abstractmethod
    def push(self, message: object):
        raise NotImplementedError("Should Implement this method.")

    @abstractmethod
    def pop(self) -> Optional[object]:
        raise NotImplementedError("Should Implement this method.")


class UnboundedMailboxQueue(AbstractQueue):
    def __init__(self):
        self._messages = queue.Queue()

    def pop(self) -> Optional[object]:
        try:
            return self._messages.get_nowait()
        except queue.Empty:
            return None

    def push(self, message: object):
        self._messages.put_nowait(message)

    def has_messages(self) -> bool:
        return not self._messages.empty()
