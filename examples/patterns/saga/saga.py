import asyncio

from examples.patterns.saga.runner import Runner
from protoactor.actor.actor_context import RootContext
from protoactor.actor.props import Props
from protoactor.actor.supervision import OneForOneStrategy, SupervisorDirective


async def main():
    context = RootContext()
    number_of_transfers = 5
    interval_between_console_updates = 1
    uptime = 99.99
    retry_attempts = 0
    refusal_probability = 0.01
    busy_probability = 0.01
    verbose = False

    props = Props.from_producer(lambda: Runner(number_of_transfers, interval_between_console_updates, uptime,
                                               refusal_probability, busy_probability, retry_attempts,
                                               verbose)).with_child_supervisor_strategy(
        OneForOneStrategy(lambda pid, reason: SupervisorDirective.Restart, retry_attempts, None)
    )

    print('Spawning runner')
    context.spawn_named(props, 'runner')
    input()


if __name__ == "__main__":
    asyncio.run(main())
