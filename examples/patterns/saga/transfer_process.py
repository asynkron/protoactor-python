import random
from datetime import timedelta

from examples.patterns.saga.account_proxy import AccountProxy
from examples.patterns.saga.messages import TransferStarted, AccountDebited, CreditRefused, AccountCredited, \
    DebitRolledBack, TransferFailed, EscalateTransfer, UnknownResult, Credit, Debit, OK, Refused, \
    FailedButConsistentResult, StatusUnknown, GetBalance, TransferCompleted, SuccessResult, FailedAndInconsistent
from protoactor.actor import PID
from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import AbstractContext, GlobalRootContext
from protoactor.actor.behavior import Behavior
from protoactor.actor.messages import Started, Stopping, Restarting, Stopped
from protoactor.actor.persistence import Event
from protoactor.actor.props import Props
from protoactor.actor.protos_pb2 import Terminated
from protoactor.persistence.persistence import Persistence
from protoactor.persistence.providers.abstract_provider import AbstractProvider


class TransferProcess(Actor):
    def __init__(self, from_id: PID, to_id: PID, amount: float, provider: AbstractProvider, persistence_id: str,
                 availability: float):
        self._from_id = from_id
        self._to_id = to_id
        self._amount = amount
        self._persistence_id = persistence_id
        self._availability = availability
        self._persistence = Persistence.with_event_sourcing(provider, self._persistence_id, self.__apply_event)
        self._behavior = Behavior()
        self._restarting = False
        self._stopping = False
        self._process_completed = False

    @staticmethod
    def __try_credit(target_actor: PID, amount: float) -> Props:
        return Props.from_producer(lambda: AccountProxy(target_actor, lambda sender: Credit(amount, sender)))

    @staticmethod
    def __try_debit(target_actor: PID, amount: float) -> Props:
        return Props.from_producer(lambda: AccountProxy(target_actor, lambda sender: Debit(amount, sender)))

    def __apply_event(self, event: Event):
        data = event.data
        print(f'Applying event: {str(data)}')
        if isinstance(data, TransferStarted):
            self._behavior.become(self.__awaiting_debit_confirmation)
        elif isinstance(data, AccountDebited):
            self._behavior.become(self.__awaiting_credit_confirmation)
        elif isinstance(data, CreditRefused):
            self._behavior.become(self.__rolling_back_debit)
        elif isinstance(data, (AccountCredited, DebitRolledBack, TransferFailed)):
            self._process_completed = True

    def __fail(self):
        comparision = random.uniform(0.0, 1.0) * 100
        return comparision > self._availability

    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        print(f'[{self._persistence_id}] Recieiving :{str(message)}')
        if isinstance(message, Started):
            # default to Starting behavior
            self._behavior.become(self.__starting)
            #  recover state from persistence - if there are any events, the current behavior
            #  should change
            await self._persistence.recover_state()
        elif isinstance(message, Stopping):
            self._stopping = True
        elif isinstance(message, Restarting):
            self._restarting = True
        elif isinstance(message, Stopped) and not self._process_completed:
            await self._persistence.persist_event(TransferFailed('Unknown. Transfer Process crashed'))
            await self._persistence.persist_event(EscalateTransfer('Unknown failure. Transfer Process crashed'))
            await context.parent.tell(UnknownResult(context.my_self))
        elif isinstance(message, Terminated) and self._restarting or self._stopping:
            # if the TransferProcess itself is restarting or stopping due to failure, we will receive a
            # Terminated message for any child actors due to them being stopped but we should not
            # treat this as a failure of the saga, so return here to stop further processing
            pass
        else:
            if self.__fail():
                raise Exception()
        # pass through all messages to the current behavior. Note this includes the Started message we
        # may have just handled as what we should do when started depends on the current behavior
        await self._behavior.receive_async(context)

    async def __starting(self, context: AbstractContext):
        if isinstance(context.message, Started):
            context.spawn_named(self.__try_debit(self._from_id, self._amount - 1), 'DebitAttempt')
            await self._persistence.persist_event(TransferStarted())

    async def __awaiting_debit_confirmation(self, context: AbstractContext):
        message = context.message
        if isinstance(message, Started):
            # if we are in this state when restarted then we need to recreate the TryDebit actor
            context.spawn_named(self.__try_debit(self._from_id, self._amount - 1), 'DebitAttempt')
        elif isinstance(message, OK):
            # good to proceed to the credit
            await self._persistence.persist_event(AccountDebited())
            context.spawn_named(self.__try_credit(self._to_id, self._amount + 1), 'CreditAttempt')
        elif isinstance(message, Refused):
            # the debit has been refused, and should not be retried
            await self._persistence.persist_event(TransferFailed('Debit refused'))
            await context.parent.tell(FailedButConsistentResult(context.my_self))
            await self.__stop_all(context)
        elif isinstance(message, Terminated):
            # the actor that is trying to make the debit has failed to respond with success we dont know why
            await self._persistence.persist_event(StatusUnknown())
            await self.__stop_all(context)

    async def __awaiting_credit_confirmation(self, context: AbstractContext):
        message = context.message
        if isinstance(message, Started):
            # if we are in this state when started then we need to recreate the TryCredit actor
            context.spawn_named(self.__try_credit(self._to_id, self._amount + 1), 'CreditAttempt')
        elif isinstance(message, OK):
            from_balance = await context.request_future(self._from_id, GetBalance(), timedelta(milliseconds=2000))
            to_balance = await context.request_future(self._to_id, GetBalance(), timedelta(milliseconds=2000))

            await self._persistence.persist_event(AccountCredited())
            await self._persistence.persist_event(
                TransferCompleted(self._from_id, from_balance, self._to_id, to_balance))

            await context.send(context.parent, SuccessResult(context.my_self))
            await self.__stop_all(context)
        elif isinstance(message, Refused):
            # sometimes a remote service might say it refuses to perform some operation.
            # This is different from a failure
            await self._persistence.persist_event(CreditRefused())
            # we have definately debited the _from account as it was confirmed, and we
            # haven't creidted to _to account, so try and rollback
            context.spawn_named(self.__try_credit(self._from_id, self._amount + 1), 'RollbackDebit')
        elif isinstance(message, Terminated):
            # the actor that is trying to make the debit has failed to respond with success we dont know why
            await self._persistence.persist_event(StatusUnknown())
            await self.__stop_all(context)

    async def __rolling_back_debit(self, context: AbstractContext):
        message = context.message
        if isinstance(message, Started):
            # if we are in this state when started then we need to recreate the TryCredit actor
            context.spawn_named(self.__try_credit(self._from_id, self._amount + 1), 'RollbackDebit')
        elif isinstance(message, OK):
            await self._persistence.persist_event(DebitRolledBack())
            await self._persistence.persist_event(TransferFailed(f'Unable to rollback debit to {self._to_id.id}'))
            await context.parent.tell(FailedButConsistentResult(context.my_self))
            await self.__stop_all(context)
        elif isinstance(message, (Refused, Terminated)):  # in between making the credit and debit, the _from account  has started refusing!! :O
            await self._persistence.persist_event(
                TransferFailed(f'Unable to rollback process. {self._from_id.id} is owed {self._amount}'))
            await self._persistence.persist_event(EscalateTransfer(f'{self._from_id.id} is owed {self._amount}'))
            await context.parent.tell(FailedAndInconsistent(context.my_self))
            await self.__stop_all(context)

    async def __stop_all(self, context: AbstractContext):
        await GlobalRootContext.stop(self._from_id)
        await GlobalRootContext.stop(self._to_id)
        await GlobalRootContext.stop(context.my_self)
