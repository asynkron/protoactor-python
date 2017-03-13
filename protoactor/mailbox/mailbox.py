from abc import ABCMeta, abstractmethod
from asyncio import sleep
from threading import RLock
from enum import Enum
from typing import Optional

from . import mailbox_statistics, messages, queue
from .. import dispatcher, invoker


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
    def start(self):
        raise NotImplementedError("Should Implement this method")


class Mailbox(AbstractMailbox):
    def __init__(self, system_messages_queue: queue.AbstractQueue, user_messages_queue: queue.AbstractQueue,
                 invoker: invoker.AbstractInvoker, dispatcher: dispatcher.AbstractDispatcher,
                 *statistics: Optional[mailbox_statistics.AbstractMailBoxStatistics]) -> None:
        self.__system_messages_queue = system_messages_queue
        self.__user_messages_queue = user_messages_queue
        self.__statistics = statistics if statistics else []
        self.__invoker = invoker
        self.__dispatcher = dispatcher
        self.__status = MailBoxStatus.IDLE
        self.__suspended = False
        self.__status_lock = RLock()

    def post_system_message(self, message: object):
        self.__system_messages_queue.push(message)
        self.__schedule()

    def post_user_message(self, message: object):
        self.__user_messages_queue.push(message)
        for stats in self.__statistics:
            stats.message_posted()
        self.__schedule()

    def start(self):
        for stats in self.__statistics:
            stats.mailbox_stated()

    def __schedule(self):
        with self.__status_lock:
            if self.__status == MailBoxStatus.IDLE:
                self.__status = MailBoxStatus.BUSY
                self.__dispatcher.schedule(self.__run)

    async def __run(self):
        while True:
            with self.__status_lock:
                if not self.__system_messages_queue.has_messages() and \
                        (self.__suspended or not self.__user_messages_queue.has_messages()):
                    self.__status = MailBoxStatus.IDLE
                    for stats in self.__statistics:
                        stats.mailbox_empty()
                    return

            await self.__process_messages()
            await sleep(0)

    async def __process_messages(self):
        throughput = self.__dispatcher.throughput
        message = None
        try:
            for i in range(throughput):
                message = self.__system_messages_queue.pop()
                if message is not None:
                    if isinstance(message, messages.SuspendMailbox):
                        self.__suspended = True
                    elif isinstance(message, messages.ResumeMailbox):
                        self.__suspended = False
                    else:
                        await self.__invoker.invoke_system_message(message)

                    if self.__suspended:
                        break

                message = self.__user_messages_queue.pop()
                if message is not None:
                    await self.__invoker.invoke_user_message(message)
                    for stats in self.__statistics:
                        stats.message_received()
                else:
                    break
        except Exception as e:
            self.__invoker.escalate_failure(e, message)
