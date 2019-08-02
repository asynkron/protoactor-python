from typing import Any

from protoactor.actor.message_header import MessageHeader

is_import = False
if is_import:
    from protoactor.actor import PID


class MessageEnvelope:
    def __init__(self, message: object, sender: 'PID' = None, header: MessageHeader = None) -> None:
        self._message = message
        self._sender = sender
        self._header = header

    @property
    def message(self) -> object:
        return self._message

    @property
    def sender(self) -> 'PID':
        return self._sender

    @property
    def header(self) -> MessageHeader:
        return self._header

    @staticmethod
    def wrap(message: Any):
        if isinstance(message, MessageEnvelope):
            return message
        return MessageEnvelope(message)

    def with_sender(self, sender: 'PID'):
        return MessageEnvelope(self.message, sender, self.header)

    def with_message(self, message: Any):
        return MessageEnvelope(message, self.sender, self.header)

    def with_header(self, header: MessageHeader = None, key: str = None, value: str = None):
        if header is not None and key is None and value is None:
            return MessageEnvelope(self.message, self.sender, header)
        elif header is None and key is not None and value is not None:
            message_header = self.header
            if message_header is None:
                message_header = MessageHeader()
            header = message_header.extend(key=key, value=value)
            return MessageEnvelope(self.message, self.sender, header)
        else:
            raise ValueError('Incorrect input value')

    def with_headers(self, items=None):
        message_header = self.header
        if message_header is None:
            message_header = MessageHeader()
        header = message_header.extend(items=items)
        return MessageEnvelope(self.message, self.sender, header)

    @staticmethod
    def unwrap(message: Any) -> Any:
        if isinstance(message, MessageEnvelope):
            return message.message, message.sender, message.header
        return message, None, None

    @staticmethod
    def unwrap_header(message: Any) -> MessageHeader:
        if isinstance(message, MessageEnvelope) and message.header is not None:
            return message.header
        return MessageHeader.empty()

    @staticmethod
    def unwrap_message(message: Any) -> Any:
        if isinstance(message, MessageEnvelope):
            return message.message
        else:
            return message

    @staticmethod
    def unwrap_sender(message: Any) -> 'PID':
        if isinstance(message, MessageEnvelope):
            return message.sender
        else:
            return None
