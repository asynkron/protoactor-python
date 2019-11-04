import asyncio
import sys

import opentracing
from jaeger_client import Tracer, Config, Span

from examples.chat.messages.chat_pb2 import Connected, SayResponse, NickResponse, Connect, NickRequest, SayRequest, \
    DESCRIPTOR
from protoactor.actor import PID
from protoactor.actor.actor_context import AbstractContext, GlobalRootContext, RootContext
from protoactor.actor.message_header import MessageHeader
from protoactor.actor.props import Props
from protoactor.remote.remote import Remote
from protoactor.remote.serialization import Serialization
from protoactor.tracing.opentracing import open_tracing_middleware
from protoactor.tracing.opentracing.open_tracing_factory import OpenTracingFactory


async def process_message(ctx: AbstractContext):
    msg = ctx.message
    if isinstance(msg, Connected):
        print(msg.message)
    elif isinstance(msg, SayResponse):
        print(f'{msg.user_name} {msg.message}')
    elif isinstance(msg, NickResponse):
        print(f'{msg.old_user_name} {msg.new_user_name}')


async def start(argv):
    tracer = init_jaeger_tracer()
    opentracing.set_global_tracer(tracer)

    middleware = open_tracing_middleware.open_tracing_sender_middleware(tracer)

    Serialization().register_file_descriptor(DESCRIPTOR)
    Remote().start("127.0.0.1", 12001)
    server = PID(address='127.0.0.1:8000', id='chatserver')
    context = RootContext(MessageHeader(), [middleware])

    props = OpenTracingFactory.get_props_with_open_tracing(Props.from_func(process_message), span_setup, span_setup,
                                                           tracer)

    client = context.spawn(props)
    await context.send(server, Connect(sender=client))

    nick = 'Alex'
    while True:
        text = input()
        if text == '/exit':
            return
        elif text.startswith('/nick '):
            new_nick = text.split(' ')[1]
            await context.send(server, NickRequest(old_user_name=nick, new_user_name=new_nick))
            nick = new_nick
        else:
            await context.send(server, SayRequest(user_name=nick, message=text))


def span_setup(span: Span, message: any):
    if message is not None:
        span.log_kv({'message': str(message)})


def init_jaeger_tracer(service_name='proto.chat.client'):
    config = Config(config={'sampler': {
        'type': 'const',
        'param': 1,
    },
        'logging': True, }, service_name=service_name, validate=True)
    return config.initialize_tracer()


def main(argv):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start(argv))
    loop.close()


if __name__ == "__main__":
    main(sys.argv[1:])
