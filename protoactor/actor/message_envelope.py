from protoactor.actor.message_header import MessageHeader


is_import = False
if is_import:
    from protoactor.actor import PID

class MessageEnvelope:
    def __init__(self, message: object, sender: 'PID' = None, header: MessageHeader = None):
        self.__message = message
        self.__sender = sender
        self.__header = header

    @property
    def message(self) -> object:
        return self.__message

    @property
    def sender(self) -> 'PID':
        return self.__sender

    @property
    def header(self) -> MessageHeader:
        return self.__header

    @staticmethod
    def wrap(message):
        if isinstance(message, MessageEnvelope):
            return message
        return MessageEnvelope(message)

    def with_sender(self, sender):
        return MessageEnvelope(self.message, sender, self.header)

    def with_message(self, message):
        return MessageEnvelope(message, self.sender, self.header)

    def with_header(self, header=None, key=None, value=None, items=None):
        if header is not None:
            return MessageEnvelope(self.message, self.sender, header)

        elif key is not None and value is not None:
            message_header = self.header
            if message_header is None:
                message_header = MessageHeader()
            header = message_header.extend(key=key, value=value)
            return MessageEnvelope(self.message, self.sender, header)

        elif items is not None:
            message_header = self.header
            if message_header is None:
                message_header = MessageHeader()
            header = message_header.extend(items=items)
            return MessageEnvelope(self.message, self.sender, header)

    @staticmethod
    def unwrap(message):
        if isinstance(message, MessageEnvelope):
            return message.message, message.sender, message.header
        return message, None, None

    @staticmethod
    def unwrap_header(message):
        if isinstance(message, MessageEnvelope) and message.header is not None:
            return message.header
        return MessageHeader.empty()

    @staticmethod
    def unwrap_message(message):
        if isinstance(message, MessageEnvelope):
            return message.message
        else:
            return message

    @staticmethod
    def unwrap_sender(message):
        if isinstance(message, MessageEnvelope):
            return message.sender
        else:
            return None
