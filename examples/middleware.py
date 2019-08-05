import time
import uuid
import asyncio

from protoactor.actor.props import Props
from protoactor.actor.actor import RootContext
from protoactor.actor.message_header import MessageHeader


async def main():
    headers = MessageHeader({'TraceID': str(uuid.uuid4()),
                             'SpanID': str(uuid.uuid4())})

    def get_middleware(next_middleware):
        async def process(context, target, envelope):
            new_envelope = envelope \
                .with_header(key='TraceID', value=context.headers.get('TraceID')) \
                .with_header(key='SpanID', value=str(uuid.uuid4())) \
                .with_header(key='ParentSpanID', value=context.headers.get('SpanID'))

            print(' 1 Enter RootContext SenderMiddleware')
            print(' 1 TraceID: ' + new_envelope.header.get('TraceID'))
            print(' 1 SpanID: ' + new_envelope.header.get('SpanID'))
            print(' 1 ParentSpanID: ' + new_envelope.header.get('ParentSpanID'))
            await next_middleware(context, target, new_envelope)
            print(' 1 Exit RootContext SenderMiddleware - Send is async, this is out of order by design')

        return process

    root = RootContext(headers, [get_middleware])

    async def actor_logic(context):
        if isinstance(context.message, str):
            print('   3 Enter Actor')
            print('   3 TraceID = ' + context.headers.get('TraceID'))
            print('   3 SpanID = ' + context.headers.get('SpanID'))
            print('   3 ParentSpanID = ' + context.headers.get('ParentSpanID'))
            print('   3 actor got = %s:%s' % (str(type(context.message)), context.message))
            await context.respond("World !")
            print('   3 Exit Actor')

    def get_receive_middleware(next_middleware):
        async def process(context, envelope):
            if isinstance(envelope.message, str):
                new_envelope = envelope \
                    .with_header(key='TraceID', value=envelope.header.get('TraceID')) \
                    .with_header(key='SpanID', value=str(uuid.uuid4())) \
                    .with_header(key='ParentSpanID', value=envelope.header.get('SpanID'))

                print('  2 Enter Actor ReceiverMiddleware')
                print('  2 TraceID: ' + new_envelope.header.get('TraceID'))
                print('  2 SpanID: ' + new_envelope.header.get('SpanID'))
                print('  2 ParentSpanID: ' + new_envelope.header.get('ParentSpanID'))
                await next_middleware(context, new_envelope)
                print('  2 Exit Actor ReceiverMiddleware')
            else:
                await next_middleware(context, envelope)

        return process

    def get_sender_middleware(next_middleware):
        async def process(context, target, envelope):
            new_envelope = envelope \
                .with_header(key='TraceID', value=context.headers.get('TraceID')) \
                .with_header(key='SpanID', value=str(uuid.uuid4())) \
                .with_header(key='ParentSpanID', value=context.headers.get('SpanID'))

            print('    4 Enter Actor SenderMiddleware')
            print('    4 TraceID: ' + new_envelope.header.get('TraceID'))
            print('    4 SpanID: ' + new_envelope.header.get('SpanID'))
            print('    4 ParentSpanID: ' + new_envelope.header.get('ParentSpanID'))
            await next_middleware(context, target, envelope)
            print('    4 Exit Actor SenderMiddleware')

        return process

    actor = Props.from_func(actor_logic)\
            .with_receive_middleware([get_receive_middleware])\
            .with_sender_middleware([get_sender_middleware])

    pid = root.spawn(actor)

    print('0 TraceID: ' + root.headers.get('TraceID'))
    print('0 SpanID: ' + root.headers.get('SpanID'))
    print('0 ParentSpanID: ' + root.headers.get('ParentSpanID', ''))

    res = await root.request_async(pid, "hello")
    print('Got result ' + res)

    await asyncio.sleep(0.5)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
