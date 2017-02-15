from abc import abstractmethod, ABCMeta
from multiprocessing import Queue


class AbstractQueue(metaclass=ABCMeta):
    @abstractmethod
    def has_messages(self) -> bool:
        raise NotImplementedError("Should Implement this method.")

    @abstractmethod
    def push(self, msg):
        raise NotImplementedError("Should Implement this method.")

    @abstractmethod
    def pop(self):
        raise NotImplementedError("Should Implement this method.")


class UnboundedMailboxQueue(AbstractQueue):
    __messages = Queue()

    def pop(self):
        try:
            return self.__messages.get_nowait()
        except Queue.empty:
            return None

    def push(self, msg):
        self.__messages.put_nowait(msg)

    def has_messages(self) -> bool:
        return not self.__messages.empty()
