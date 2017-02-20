from .process import AbstractProcess
from .process_registry import ProcessRegistry


class PID:
    def __init__(self, address: str, id: str, ref: AbstractProcess) -> None:
        self.__address = address
        self.__id = id
        self.__process: AbstractProcess = ref

    @property
    def address(self):
        return self.__address

    @property
    def id(self):
        return self.__id

    @property
    def process(self) -> AbstractProcess:
        return self.__process

    @process.setter
    def process(self, ref: AbstractProcess) -> None:
        self.__process = ref

    def __repr__(self):
        return "{} / {}".format(self.__address, self.__id)

    def tell(self, msg):
        if not self.__process:
            self.__process = ProcessRegistry.get(self)

        self.__process.send_user_message(self, msg)

    def send_system_message(self, sys):
        pass

    def stop(self):
        self.__process.stop()
