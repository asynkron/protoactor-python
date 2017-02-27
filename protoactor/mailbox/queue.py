from abc import abstractmethod, ABCMeta
from multiprocessing import Queue
from queue import Empty
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
        # TODO multiprocess.Queue empty() and full() are not reliable, Seek otherways.
        self.__messages = Queue()

    def pop(self) -> Optional[object]:
        try:
            return self.__messages.get_nowait()
        except Empty:
            return None

    def push(self, message: object):
        self.__messages.put(message)

    def has_messages(self) -> bool:
        # TODO multiprocess.Queue empty() and full() are not reliable, Seek otherways.
        return not self.__messages.empty()
