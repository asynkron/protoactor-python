from abc import ABCMeta, abstractmethod
from enum import Enum
from asyncio import sleep
from .mailbox_statistics import AbstractMailBoxStatistics
from .messages import SuspendMailbox, ResumeMailbox
from .queue import AbstractQueue
from ..dispatcher import AbstractDispatcher
from ..invoker import AbstractInvoker


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
    def register_handlers(self, invoker, dispatcher):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def start(self):
        raise NotImplementedError("Should Implement this method")


class Mailbox(AbstractMailbox):
    def __init__(self, system_messages_queue: AbstractQueue, user_messages_queue: AbstractQueue,
                 statistics: [AbstractMailBoxStatistics] = None):
        self.__system_messages_queue = system_messages_queue
        self.__user_messages_queue = user_messages_queue
        self.__statistics = statistics if statistics else []
        self.__invoker: AbstractInvoker = None
        self.__dispatcher: AbstractDispatcher = None
        self.__status = MailBoxStatus.IDLE
        self.__suspended: bool = False

    def register_handlers(self, invoker: AbstractInvoker, dispatcher: AbstractDispatcher):
        self.__invoker = invoker
        self.__dispatcher = dispatcher

    # TODO check if invoker and dispatcher are set before calling __schedule
    def post_system_message(self, message: object):
        self.__system_messages_queue.push(message)
        self.__schedule()

    # TODO check if invoker and dispatcher are set before calling __schedule
    def post_user_message(self, message: object):
        self.__user_messages_queue.push(message)
        for stats in self.__statistics:
            stats.message_posted()
        self.__schedule()

    def start(self):
        for stats in self.__statistics:
            stats.mailbox_stated()

    def __schedule(self):
        if self.__status == MailBoxStatus.IDLE:
            self.__status = MailBoxStatus.BUSY
            self.__dispatcher.schedule(self.__run)

    async def __run(self):
        while self.__system_messages_queue.has_messages() or (not self.__suspended and self.__user_messages_queue.has_messages()):
            await self.__process_messages()
            self.__status = MailBoxStatus.IDLE
            sleep(0)

        for stats in self.__statistics:
            stats.mailbox_empty()


    async def __process_messages(self):
        throughput = self.__dispatcher.throughput
        message = None
        try:
            for i in range(throughput):
                message = self.__system_messages_queue.pop()
                if message:
                    if isinstance(message, SuspendMailbox):
                        self.__suspended = True
                    elif isinstance(message, ResumeMailbox):
                        self.__suspended = False
                    else:
                        await self.__invoker.invoke_system_message(message)

                    if self.__suspended:
                        break

                message = self.__user_messages_queue.pop()
                if message:
                    for stats in self.__statistics:
                        stats.message_received()

                    await self.__invoker.invoke_user_message(message)
                else:
                    break
        except Exception as e:
            self.__invoker.escalate_failure(e, message)
