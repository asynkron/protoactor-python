from abc import abstractmethod, ABCMeta
from asyncio import Queue, QueueEmpty
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
        self.__messages = Queue()

    def pop(self) -> Optional[object]:
        try:
            return self.__messages.get_nowait()
        except QueueEmpty:
            return None

    def push(self, message: object):
        self.__messages.put_nowait(message)

    def has_messages(self) -> bool:
        return not self.__messages.empty()
