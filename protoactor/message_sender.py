from . import pid

class MessageSender:
    def __init__(self, message: object, sender: pid.PID) -> None:
        self.__message = message
        self.__sender = sender

    @property
    def sender(self) -> pid.PID:
        return self.__sender

    @property
    def message(self) -> object:
        return self.__message