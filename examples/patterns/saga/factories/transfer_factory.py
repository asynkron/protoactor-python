from examples.patterns.saga.transfer_process import TransferProcess
from protoactor.actor import PID
from protoactor.actor.actor_context import AbstractContext
from protoactor.actor.props import Props
from protoactor.actor.supervision import OneForOneStrategy, SupervisorDirective
from protoactor.persistence.providers.abstract_provider import AbstractProvider


class TransferFactory:
    def __init__(self, context: AbstractContext, provider: AbstractProvider, availability: float, retry_attempts: int):
        self._context = context
        self._provider = provider
        self._availability = availability
        self._retry_attempts = retry_attempts

    def create_transfer(self, actor_name: str, from_account: PID, to_account: PID, amount: float,
                        persistence_id: str) -> PID:
        transfer_props = Props.from_producer(
            lambda: TransferProcess(from_account, to_account, amount, self._provider, persistence_id,
                                    self._availability)).with_child_supervisor_strategy(
            OneForOneStrategy(lambda pid, reason: SupervisorDirective.Restart, self._retry_attempts, None))
        transfer = self._context.spawn_named(transfer_props, actor_name)
        return transfer
