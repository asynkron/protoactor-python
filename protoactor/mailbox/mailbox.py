from abc import ABCMeta, abstractmethod
from enum import Enum
from threading import RLock, Event
from typing import Optional

from protoactor.actor.messages import SuspendMailbox, ResumeMailbox
from protoactor.mailbox import mailbox_statistics
from protoactor.mailbox.dispatcher import AbstractDispatcher, AbstractMessageInvoker
from protoactor.mailbox.mailbox_statistics import AbstractMailBoxStatistics
from protoactor.mailbox.queue import AbstractQueue, UnboundedMailboxQueue


class MailBoxStatus(Enum):
    IDLE = 0
    BUSY = 1


class AbstractMailbox(metaclass=ABCMeta):
    @abstractmethod
    def post_user_message(self, msg):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def post_system_message(self, msg):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def register_handlers(self, invoker: AbstractMessageInvoker, dispatcher: AbstractDispatcher):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def start(self):
        raise NotImplementedError("Should Implement this method")


class DefaultMailbox(AbstractMailbox):
    def __init__(self, system_messages_queue: AbstractQueue,
                 user_messages_queue: AbstractQueue,
                 statistics: [AbstractMailBoxStatistics]) -> None:
        self._system_messages_queue = system_messages_queue
        self._user_messages_queue = user_messages_queue
        self._statistics = statistics

        self._event = Event()
        self._invoker = None
        self._dispatcher = None

        self._system_message_count = 0
        self._suspended = False

    def post_user_message(self, message: object):
        self._user_messages_queue.push(message)
        for stats in self._statistics:
            stats.message_posted(message)
        self.__schedule()

    def post_system_message(self, message: object):
        self._system_messages_queue.push(message)
        self._system_message_count += 1
        for stats in self._statistics:
            stats.message_posted(message)
        self.__schedule()

    def register_handlers(self, invoker: AbstractMessageInvoker, dispatcher: AbstractDispatcher):
        self._invoker = invoker
        self._dispatcher = dispatcher
        self._dispatcher.schedule(self.__run)

    def start(self):
        for stats in self._statistics:
            stats.mailbox_stated()

    async def __run(self):
        while True:
            self._event.wait()
            await self.__process_messages()
            self._event.clear()

            if self._system_messages_queue.has_messages() or \
                    (not self._suspended and self._user_messages_queue.has_messages()):
                self.__schedule()
            else:
                for stats in self._statistics:
                    stats.mailbox_empty()

    async def __process_messages(self):
        message = None
        try:
            for i in range(self._dispatcher.throughput):
                message = self._system_messages_queue.pop()
                if message is not None:
                    if isinstance(message, SuspendMailbox):
                        self._suspended = True
                    elif isinstance(message, ResumeMailbox):
                        self._suspended = False
                    else:
                        await self._invoker.invoke_system_message(message)
                        for stats in self._statistics:
                            stats.message_received(message)
                    if self._suspended:
                        break

                message = self._user_messages_queue.pop()
                if message is not None:
                    await self._invoker.invoke_user_message(message)
                    for stats in self._statistics:
                        stats.message_received(message)
                else:
                    break
        except Exception as e:
            await self._invoker.escalate_failure(e, message)

    def __schedule(self):
        self._event.set()


class SynchronousMailbox(AbstractMailbox):
    def __init__(self, system_messages_queue: AbstractQueue,
                 user_messages_queue: AbstractQueue,
                 statistics: [AbstractMailBoxStatistics]) -> None:
        self.__system_messages_queue = system_messages_queue
        self.__user_messages_queue = user_messages_queue
        self.__statistics = statistics

        self.__invoker = None
        self.__dispatcher = None

        self.__status = MailBoxStatus.IDLE
        self.__system_message_count = 0
        self.__suspended = False
        self.__lock = RLock()

    def post_user_message(self, message: object):
        self.__user_messages_queue.push(message)
        for stats in self.__statistics:
            stats.message_posted(message)
        self.__schedule()

    def post_system_message(self, message: object):
        self.__system_messages_queue.push(message)
        with self.__lock:
            self.__system_message_count += 1
        for stats in self.__statistics:
            stats.message_posted(message)
        self.__schedule()

    def register_handlers(self, invoker: AbstractMessageInvoker, dispatcher: AbstractDispatcher):
        self.__invoker = invoker
        self.__dispatcher = dispatcher

    def start(self):
        for stats in self.__statistics:
            stats.mailbox_stated()

    async def __run(self):
        await self.__process_messages()

        with self.__lock:
            self.__status = MailBoxStatus.IDLE

        if self.__system_messages_queue.has_messages() or \
                (not self.__suspended and self.__user_messages_queue.has_messages()):
            self.__schedule()

        for stats in self.__statistics:
            stats.mailbox_empty()

    async def __process_messages(self):
        message = None
        try:
            for i in range(self.__dispatcher.throughput):
                message = self.__system_messages_queue.pop()
                if message is not None:
                    if isinstance(message, SuspendMailbox):
                        self.__suspended = True
                    elif isinstance(message, ResumeMailbox):
                        self.__suspended = False
                    else:
                        await self.__invoker.invoke_system_message(message)
                        for stats in self.__statistics:
                            stats.message_received(message)
                    if self.__suspended:
                        break

                message = self.__user_messages_queue.pop()
                if message is not None:
                    await self.__invoker.invoke_user_message(message)
                    for stats in self.__statistics:
                        stats.message_received(message)
                else:
                    break
        except Exception as e:
            await self.__invoker.escalate_failure(e, message)

    def __schedule(self):
        with self.__lock:
            if self.__status == MailBoxStatus.IDLE:
                execute = True
                self.__status = MailBoxStatus.BUSY
            else:
                execute = False

        if execute:
            self.__dispatcher.schedule(self.__run)


class MailboxFactory():
    @staticmethod
    def create_bounded_mailbox(size: int,
                               *stats: Optional[mailbox_statistics.AbstractMailBoxStatistics]) -> AbstractMailbox:
        pass

    @staticmethod
    def create_unbounded_mailbox(*stats: Optional[mailbox_statistics.AbstractMailBoxStatistics]) -> AbstractMailbox:
        statistics = stats if stats else []
        return DefaultMailbox(UnboundedMailboxQueue(), UnboundedMailboxQueue(), statistics)

    @staticmethod
    def create_unbounded_synchronous_mailbox(*stats: Optional[mailbox_statistics.AbstractMailBoxStatistics]) -> \
            AbstractMailbox:
        statistics = stats if stats else []
        return SynchronousMailbox(UnboundedMailboxQueue(), UnboundedMailboxQueue(), statistics)
