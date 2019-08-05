from typing import Callable, Any
from uuid import uuid4

from protoactor.actor.log import get_logger
from protoactor.actor.messages import DeadLetterEvent
from protoactor.actor.utils import singleton

from protoactor.mailbox.dispatcher import Dispatchers, AbstractDispatcher


class Subscription():
    def __init__(self, event_stream, action, dispatcher):
        self.__event_stream = event_stream
        self.__dispatcher = dispatcher
        self.__action = action
        self.__id = uuid4()

    @property
    def id(self):
        return self.__id

    @property
    def dispatcher(self):
        return self.__dispatcher

    @property
    def action(self):
        return self.__action

    def unsubscribe(self):
        self.__event_stream.unsubscribe(self.__id)


class EventStream():
    def __init__(self):
        self._subscriptions = {}
        self._logger = get_logger('EventStream')
        self.subscribe(self.__report_deadletters, DeadLetterEvent)

    def subscribe(self, fun: Callable[..., Any], msg_type: type = None,
                  dispatcher: AbstractDispatcher = Dispatchers().synchronous_dispatcher) -> Subscription:
        async def action(msg):
            if msg_type is None:
                await fun(msg)
            elif isinstance(msg, msg_type):
                await fun(msg)

        sub = Subscription(self, action, dispatcher)
        self._subscriptions[sub.id] = sub
        return sub

    def publish(self, message: object) -> None:
        for sub in self._subscriptions.values():
            async def action():
                try:
                    await sub.action(message)
                except Exception:
                    self._logger.log_warning('Exception has occurred when publishing a message.')
            sub.dispatcher.schedule(action)

    def unsubscribe(self, uniq_id):
        del self._subscriptions[uniq_id]

    async def __report_deadletters(self, message: DeadLetterEvent) -> None:
        console_message = """[DeadLetterEvent] %(pid)s got %(message_type)s:%(message)s from
        %(sender)s""" % {"pid": message.pid,
                         "message_type": type(message.message),
                         "message": message.message,
                         "sender": message.sender
                         }
        self._logger.info(console_message)


class GlobalEventStream(metaclass=singleton):
    def __init__(self):
        self.__instance = EventStream()

    @property
    def instance(self):
        return self.__instance
