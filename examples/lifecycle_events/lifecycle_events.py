import asyncio

import opentracing
from jaeger_client import Config

from protoactor.actor.actor import Actor
from protoactor.actor.actor_context import RootContext, AbstractContext, GlobalRootContext
from protoactor.actor.event_stream import GlobalEventStream
from protoactor.actor.messages import DeadLetterEvent, Started, Stopping, Stopped, Restarting
from protoactor.actor.props import Props
from protoactor.tracing.opentracing.open_tracing_factory import OpenTracingFactory
from protoactor.tracing.opentracing.open_tracing_middleware import open_tracing_sender_middleware


class Hello:
    def __init__(self, who: str):
        self.who = who


class ChildActor(Actor):
    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, Hello):
            print(f"Hello {message.who}")
        elif isinstance(message, Started):
            print(f"Started, initialize actor here")
        elif isinstance(message, Stopping):
            print(f"Stopping, actor is about shut down")
        elif isinstance(message, Stopped):
            print(f"Stopped, actor and it's children are stopped")
        elif isinstance(message, Restarting):
            print(f"Restarting, actor is about restart")


async def main():
    tracer = init_jaeger_tracer()
    opentracing.set_global_tracer(tracer)
    GlobalEventStream.subscribe(process_dead_letter_event, DeadLetterEvent)

    context = RootContext(middleware=[open_tracing_sender_middleware()])

    props = Props.from_producer(lambda: ChildActor())
    props = OpenTracingFactory.get_props_with_open_tracing(props)

    actor = context.spawn(props)
    await context.send(actor, Hello(who="Alex"))

    await asyncio.sleep(1)
    await GlobalRootContext.stop_future(actor)

    input()

async def process_dead_letter_event(msg: DeadLetterEvent) -> None:
    if msg.message is not None:
        print(f"DeadLetter from {msg.sender} to {msg.pid} : {type(msg.message).__name__} = '{str(msg.message)}'")
    else:
        print(f"DeadLetter from {msg.sender} to {msg.pid}")


def init_jaeger_tracer(service_name='proto.example.lifecycle_events'):
    config = Config(config={'sampler': {
        'type': 'const',
        'param': 1,
    },
        'logging': True, }, service_name=service_name, validate=True)
    return config.initialize_tracer()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
