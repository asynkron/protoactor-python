import logging
from typing import Callable, Any
from uuid import uuid4

from protoactor.actor import log
from protoactor.actor.messages import DeadLetterEvent

from protoactor.mailbox.dispatcher import Dispatchers, AbstractDispatcher


class Subscription():
    def __init__(self, event_stream, action, dispatcher):
        self._event_stream = event_stream
        self._dispatcher = dispatcher
        self._action = action
        self._id = uuid4()

    @property
    def id(self):
        return self._id

    @property
    def dispatcher(self):
        return self._dispatcher

    @property
    def action(self):
        return self._action

    def unsubscribe(self):
        self._event_stream.unsubscribe(self._id)


class EventStream():
    def __init__(self):
        self._subscriptions = {}
        self._logger = log.create_logger(logging.INFO, context=EventStream)
        self.subscribe(self.__process_dead_letters, DeadLetterEvent)

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

    async def publish(self, message: object) -> None:
        for sub in self._subscriptions.values():
            try:
                await sub.action(message)
            except Exception:
                self._logger.exception('Exception has occurred when publishing a message.')

    def unsubscribe(self, uniq_id):
        del self._subscriptions[uniq_id]

    async def __process_dead_letters(self, message: DeadLetterEvent) -> None:
        self._logger.info(f'[DeadLetter] {message.pid.to_short_string()} got {type(message.message)}:{message.message} '
                          f'from {message.sender}')


GlobalEventStream = EventStream()

# class GlobalEventStream(metaclass=Singleton):
#     def __init__(self):
#         self.__instance = EventStream()
#
#     @property
#     def instance(self):
#         return self.__instance
