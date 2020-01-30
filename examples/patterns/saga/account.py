import asyncio
import random
from datetime import timedelta
from enum import Enum

from examples.patterns.saga.messages import Credit, Debit, InsufficientFunds, GetBalance, Refused, ServiceUnavailable, \
    InternalServerError, OK
from protoactor.actor import PID
from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import AbstractContext


class Behavior(Enum):
    FAIL_BEFORE_PROCESSING = 1
    FAIL_AFTER_PROCESSING = 2
    PROCESS_SECCESS_FULLY = 3


class Account(Actor):
    def __init__(self, name: str, service_uptime: float, refusal_probability: float, busy_probability: float):
        self._name = name
        self._service_uptime = service_uptime
        self._refusal_probability = refusal_probability
        self._busy_probability = busy_probability
        self._random = random
        self._balance = 10
        self._processed_messages = {}

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if isinstance(msg, Credit) and self.__already_processed(msg.reply_to):
            await self.__reply(msg.reply_to)
        elif isinstance(msg, Credit):
            await self.__adjust_balance(msg.reply_to, msg.amount)
        elif isinstance(msg, Debit) and self.__already_processed(msg.reply_to):
            await self.__reply(msg.reply_to)
        elif isinstance(msg, Debit) and msg.amount + self._balance >= 0:
            await self.__adjust_balance(msg.reply_to, msg.amount)
        elif isinstance(msg, Debit):
            await msg.reply_to.tell(InsufficientFunds())
        elif isinstance(msg, GetBalance):
            await context.respond(self._balance)

    async def __reply(self, reply_to: PID):
        await reply_to.tell(self._processed_messages[reply_to.to_short_string()])

    async def __adjust_balance(self, reply_to: PID, amount: float):
        if self.__refuse_permanently():
            self._processed_messages[reply_to.to_short_string()] = Refused()
            await reply_to.tell(Refused())

        if self.__busy():
            await reply_to.tell(ServiceUnavailable())

        # generate the behavior to be used whilst processing this message
        behaviour = self.__determine_processing_behavior()
        if behaviour == Behavior.FAIL_BEFORE_PROCESSING:
            await self.__failure(reply_to)

        await asyncio.sleep(timedelta(milliseconds=random.randint(0, 150)).total_seconds())

        self._balance += amount
        self._processed_messages[reply_to.to_short_string()] = OK()

        # simulate chance of failure after applying the change. This will
        # force a retry of the operation which will test the operation
        # is idempotent
        if behaviour == Behavior.FAIL_AFTER_PROCESSING:
            await self.__failure(reply_to)

        await reply_to.tell(OK())

    def __busy(self):
        comparision = random.uniform(0.0, 1.0)
        return comparision <= self._busy_probability

    def __refuse_permanently(self):
        comparision = random.uniform(0.0, 1.0)
        return comparision <= self._refusal_probability

    async def __failure(self, reply_to: PID):
        await reply_to.tell(InternalServerError())

    def __determine_processing_behavior(self):
        comparision = random.uniform(0.0, 1.0)
        if comparision > self._service_uptime:
            if random.uniform(0.0, 1.0) * 100 > 50:
                return Behavior.FAIL_BEFORE_PROCESSING
            else:
                return Behavior.FAIL_AFTER_PROCESSING
        else:
            return Behavior.PROCESS_SECCESS_FULLY

    def __already_processed(self, reply_to: PID):
        return reply_to.to_short_string() in self._processed_messages
