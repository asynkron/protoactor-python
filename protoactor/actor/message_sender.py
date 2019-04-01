from protoactor.actor.protos_pb2 import PID


class MessageSender:
    def __init__(self, message: object, sender: PID) -> None:
        self.__message = message
        self.__sender = sender

    @property
    def sender(self) -> PID:
        return self.__sender

    @property
    def message(self) -> object:
        return self.__message
