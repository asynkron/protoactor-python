import asyncio
import threading
from abc import ABCMeta, abstractmethod
from enum import Enum
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

        self._event = threading.Event()
        self._async_event = None
        self._loop = None

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
        self._event.wait()

    def start(self):
        for stats in self._statistics:
            stats.mailbox_stated()

    def initialize(self):
        self._loop = asyncio.get_event_loop()
        self._async_event = asyncio.Event()
        self._event.set()

    async def __run(self):
        self.initialize()

        while True:
            await self._async_event.wait()
            await self.__process_messages()
            self._async_event.clear()

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

    async def notify(self) -> None:
        self._async_event.set()

    def __schedule(self):
        self._loop.call_soon_threadsafe(lambda: self._async_event.set())


# SynchronousMailbox

# class DefaultMailbox(AbstractMailbox):
#     def __init__(self, system_messages_queue: AbstractQueue,
#                  user_messages_queue: AbstractQueue,
#                  statistics: [AbstractMailBoxStatistics]) -> None:
#         self._system_messages_queue = system_messages_queue
#         self._user_messages_queue = user_messages_queue
#         self._statistics = statistics
#
#         self._invoker = None
#         self._dispatcher = None
#
#         self._status = MailBoxStatus.IDLE
#         self._system_message_count = 0
#         self._suspended = False
#         self._lock = RLock()
#
#     def post_user_message(self, message: object):
#         self._user_messages_queue.push(message)
#         for stats in self._statistics:
#             stats.message_posted(message)
#         self.__schedule()
#
#     def post_system_message(self, message: object):
#         self._system_messages_queue.push(message)
#         with self._lock:
#             self._system_message_count += 1
#         for stats in self._statistics:
#             stats.message_posted(message)
#         self.__schedule()
#
#     def register_handlers(self, invoker: AbstractMessageInvoker, dispatcher: AbstractDispatcher):
#         self._invoker = invoker
#         self._dispatcher = dispatcher
#
#     def start(self):
#         for stats in self._statistics:
#             stats.mailbox_stated()
#
#     async def __run(self):
#         await self.__process_messages()
#
#         with self._lock:
#             self._status = MailBoxStatus.IDLE
#
#         if self._system_messages_queue.has_messages() or \
#                 (not self._suspended and self._user_messages_queue.has_messages()):
#             self.__schedule()
#
#         await asyncio.gather(*asyncio.Task.all_tasks())
#
#         for stats in self._statistics:
#             stats.mailbox_empty()
#
#     async def __process_messages(self):
#         message = None
#         try:
#             for i in range(self._dispatcher.throughput):
#                 message = self._system_messages_queue.pop()
#                 if message is not None:
#                     if isinstance(message, SuspendMailbox):
#                         self._suspended = True
#                     elif isinstance(message, ResumeMailbox):
#                         self._suspended = False
#                     else:
#                         await self._invoker.invoke_system_message(message)
#                         for stats in self._statistics:
#                             stats.message_received(message)
#                     if self._suspended:
#                         break
#
#                 message = self._user_messages_queue.pop()
#                 if message is not None:
#                     await self._invoker.invoke_user_message(message)
#                     for stats in self._statistics:
#                         stats.message_received(message)
#                 else:
#                     break
#         except Exception as e:
#             await self._invoker.escalate_failure(e, message)
#
#     def __schedule(self):
#         with self._lock:
#             if self._status == MailBoxStatus.IDLE:
#                 execute = True
#                 self._status = MailBoxStatus.BUSY
#             else:
#                 execute = False
#
#         if execute:
#             self._dispatcher.schedule(self.__run)


class MailboxFactory():
    @staticmethod
    def create_bounded_mailbox(size: int,
                               *stats: Optional[mailbox_statistics.AbstractMailBoxStatistics]) -> AbstractMailbox:
        pass

    @staticmethod
    def create_unbounded_mailbox(*stats: Optional[mailbox_statistics.AbstractMailBoxStatistics]) -> AbstractMailbox:
        statistics = stats if stats else []
        return DefaultMailbox(UnboundedMailboxQueue(), UnboundedMailboxQueue(), statistics)

    # @staticmethod
    # def create_unbounded_synchronous_mailbox(*stats: Optional[mailbox_statistics.AbstractMailBoxStatistics]) -> \
    #         AbstractMailbox:
    #     statistics = stats if stats else []
    #     return SynchronousMailbox(UnboundedMailboxQueue(), UnboundedMailboxQueue(), statistics)
