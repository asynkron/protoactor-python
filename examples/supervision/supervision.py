import asyncio
import logging
import sys
import traceback

from protoactor.actor import PID, log
from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import AbstractContext, RootContext
from protoactor.actor.messages import Started, Stopping, Stopped
from protoactor.actor.props import Props
from protoactor.actor.protos_pb2 import Terminated
from protoactor.actor.supervision import SupervisorDirective, OneForOneStrategy


class Hello:
    def __init__(self, who: str):
        self.who = who


class Fatal:
    pass


class Recoverable:
    pass


class FatalException(Exception):
    pass


class RecoverableException(Exception):
    pass


class Decider:
    @staticmethod
    def decide(pid: PID, reason: Exception):
        if isinstance(reason, RecoverableException):
            return SupervisorDirective.Restart
        elif isinstance(reason, FatalException):
            return SupervisorDirective.Stop
        else:
            return SupervisorDirective.Escalate


class ChildActor(Actor):
    def __init__(self):
        self._logger = log.create_logger(logging.DEBUG, context=ChildActor)

    async def receive(self, context: AbstractContext):
        msg = context.message

        if isinstance(msg, Hello):
            self._logger.debug(f'Hello {msg.who}')
        elif isinstance(msg, Recoverable):
            raise RecoverableException()
        elif isinstance(msg, Fatal):
            raise FatalException()
        elif isinstance(msg, Started):
            self._logger.debug('Started, initialize actor here')
        elif isinstance(msg, Stopping):
            self._logger.debug('Stopping, actor is about shut down')
        elif isinstance(msg, Stopped):
            self._logger.debug("Stopped, actor and it's children are stopped")
        elif isinstance(msg, Stopping):
            self._logger.debug('Restarting, actor is about restart')


class ParentActor(Actor):
    def __init__(self):
        pass

    async def receive(self, context: AbstractContext):
        if context.children is None or len(context.children) == 0:
            props = Props.from_producer(lambda: ChildActor())
            child = context.spawn(props)
        else:
            child = context.children[0]

        msg = context.message
        if isinstance(msg, Hello) or \
           isinstance(msg, Recoverable) or \
           isinstance(msg, Fatal):
            await context.forward(child)
        elif isinstance(msg, Terminated):
            print(f'Watched actor was Terminated, {msg.who}')


async def main():
    context = RootContext()

    logging.basicConfig(
        format='%(name)s - %(levelname)s - %(message)s %(stack_info)s',
        level=logging.DEBUG,
        handlers = [logging.StreamHandler(sys.stdout)]
    )

    props = Props.from_producer(lambda: ParentActor()).with_child_supervisor_strategy(OneForOneStrategy(Decider.decide,
                                                                                                        1, None))
    actor = context.spawn(props)
    await context.send(actor, Hello('Alex'))
    await context.send(actor, Recoverable())
    await context.send(actor, Fatal())

    await asyncio.sleep(1)
    await context.stop(actor)

    input()


if __name__ == "__main__":
    asyncio.run(main())
