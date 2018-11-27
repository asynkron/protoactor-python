import asyncio

from protoactor import actor
from protoactor.context import RootContext


class HelloMessage:
    def __init__(self, text: str):
        self.text = text


async def hello_function(context):
    message = context.message
    if isinstance(message, HelloMessage):
        context.respond("hey")


async def main():
    context = RootContext()
    props = actor.from_func(hello_function)
    pid = actor.spawn(props)

    reply = await context.request_async(pid, HelloMessage('Hello'))
    print(reply)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
