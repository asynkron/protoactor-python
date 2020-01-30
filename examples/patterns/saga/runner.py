import asyncio

from examples.patterns.saga.account import Account
from examples.patterns.saga.factories.transfer_factory import TransferFactory
from examples.patterns.saga.in_memory_provider import InMemoryProvider
from examples.patterns.saga.internal.for_with_progress import ForWithProgress
from examples.patterns.saga.messages import SuccessResult, UnknownResult, FailedAndInconsistent, \
    FailedButConsistentResult
from protoactor.actor import PID
from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import RootContext, AbstractContext
from protoactor.actor.messages import Started
from protoactor.actor.props import Props


class Runner(Actor):
    def __init__(self, number_of_iterations: int, interval_between_console_updates: int, uptime: float,
                 refusal_probability: float, busy_probability: float, retry_attempts: int, verbose: bool):
        self._context = RootContext()
        self._number_of_iterations = number_of_iterations
        self._interval_between_console_updates = interval_between_console_updates
        self._uptime = uptime
        self._refusal_probability = refusal_probability
        self._busy_probability = busy_probability
        self._retry_attempts = retry_attempts
        self._verbose = verbose

        self._transfers = []
        self._success_results = 0
        self._failed_and_inconsistent_results = 0
        self._failed_but_consistent_results = 0
        self._unknown_results = 0
        self._in_memory_provider = None

    def __create_account(self, name: str) -> PID:
        account_props = Props.from_producer(lambda: Account(name,
                                                            self._uptime,
                                                            self._refusal_probability,
                                                            self._busy_probability))
        return self._context.spawn_named(account_props, name)

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if isinstance(msg, SuccessResult):
            self._success_results += 1
            await self.__check_for_completion(msg.pid)
        elif isinstance(msg, UnknownResult):
            self._unknown_results += 1
            await self.__check_for_completion(msg.pid)
        elif isinstance(msg, FailedAndInconsistent):
            self._failed_and_inconsistent_results += 1
            await self.__check_for_completion(msg.pid)
        elif isinstance(msg, FailedButConsistentResult):
            self._failed_but_consistent_results += 1
            await self.__check_for_completion(msg.pid)
        elif isinstance(msg, Started):
            self._in_memory_provider = InMemoryProvider()

            def every_nth_action(i: int):
                print(f'Started {i}/{self._number_of_iterations} processes')

            def every_action(i: int, nth: bool):
                j = i
                from_account = self.__create_account(f'FromAccount{j}')
                to_account = self.__create_account(f'ToAccount{j}')
                actor_name = f'Transfer Process {j}'
                persistance_id = f'Transfer Process {j}'
                factory = TransferFactory(context, self._in_memory_provider, self._uptime, self._retry_attempts)
                transfer = factory.create_transfer(actor_name, from_account, to_account, 10, persistance_id)
                self._transfers.append(transfer)
                if i == self._number_of_iterations and not nth:
                    print(f'Started {j}/{self._number_of_iterations} proesses')

            ForWithProgress(self._number_of_iterations, self._interval_between_console_updates, True, False).every_nth(
                every_nth_action, every_action)

    async def __check_for_completion(self, pid: PID):
        self._transfers.remove(pid)
        remaining = len(self._transfers)
        if self._number_of_iterations >= self._interval_between_console_updates:
            print('.')
            if remaining % (self._number_of_iterations / self._interval_between_console_updates) == 0:
                print()
                print(f'{remaining} processes remaining')
            else:
                print(f'{remaining} processes remaining')
            if remaining == 0:
                await asyncio.sleep(0.25)
                print()
                print(f'RESULTS for {self._uptime}% uptime, {self._refusal_probability}% chance of refusal, '
                      f'{self._busy_probability}% of being busy and {self._retry_attempts} retry attempts:')

                print(f'{self.__as_percentage(self._number_of_iterations, self._success_results)}% '
                      f'({self._success_results}/{self._number_of_iterations}) successful transfers')

                print(f'{self.__as_percentage(self._number_of_iterations, self._failed_but_consistent_results)}% '
                      f'({self._failed_but_consistent_results}/{self._number_of_iterations}) '
                      f'failures leaving a consistent system')

                print(f'{self.__as_percentage(self._number_of_iterations, self._failed_and_inconsistent_results)}% '
                      f'({self._failed_and_inconsistent_results}/{self._number_of_iterations}) '
                      f'failures leaving an inconsistent system')

                print(f'{self.__as_percentage(self._number_of_iterations, self._unknown_results)}% '
                      f'({self._unknown_results}/{self._number_of_iterations}) unknown results')

                if self._verbose:
                    for stream in self._in_memory_provider.events:
                        print()
                        print(f'Event log for {stream.key}')
                        for event in stream.value:
                            print(event.value)

    def __as_percentage(self, number_of_iterations: float, results: float):
        return (results / number_of_iterations) * 100
