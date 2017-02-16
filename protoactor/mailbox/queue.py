from abc import abstractmethod, ABCMeta
from multiprocessing import Queue
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
    __messages = Queue()

    def pop(self) -> Optional[object]:
        try:
            return self.__messages.get_nowait()
        except Queue.empty:
            return None

    def push(self, message: object):
        self.__messages.put_nowait(message)

    def has_messages(self) -> bool:
        return not self.__messages.empty()
