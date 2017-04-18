from . import protos_pb2

class MessageSender:
    def __init__(self, message: object, sender: protos_pb2.PID) -> None:
        self.__message = message
        self.__sender = sender

    @property
    def sender(self) -> protos_pb2.PID:
        return self.__sender

    @property
    def message(self) -> object:
        return self.__message