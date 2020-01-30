from datetime import timedelta
from typing import Callable, Any

from examples.patterns.saga.messages import OK, Refused, InsufficientFunds, InternalServerError, ServiceUnavailable
from protoactor.actor import PID
from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import AbstractContext
from protoactor.actor.messages import Started, ReceiveTimeout


class AccountProxy(Actor):
    def __init__(self,target:PID, create_message:Callable[[PID], Any]):
        self._target = target
        self._create_message = create_message

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if isinstance(msg, Started):
            # imagine this is some sort of remote call rather than a local actor call
            await self._target.tell(self._create_message(context.my_self))
            context.set_receive_timeout(timedelta(milliseconds=100))
        elif isinstance(msg, OK):
            context.cancel_receive_timeout()
            await context.parent.tell(msg)
        elif isinstance(msg, Refused):
            context.cancel_receive_timeout()
            await context.parent.tell(msg)
        # This emulates a failed remote call
        elif isinstance(msg, (InsufficientFunds,
                              InternalServerError,
                              ReceiveTimeout,
                              ServiceUnavailable)):
            raise Exception()