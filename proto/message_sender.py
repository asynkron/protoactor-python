from .pid import PID

class MessageSender:
    def __init__(self, message: object, sender: PID):
        self.__message = message
        self.__sender= sender

    @property
    def sender(self):
        return self.__sender

    @property
    def message(self):
        return self.__message