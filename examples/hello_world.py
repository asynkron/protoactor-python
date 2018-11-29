from protoactor import actor, context
from protoactor.context import RootContext
from protoactor.props import Props


class HelloMessage:
    def __init__(self, text: str):
        self.text = text


class HelloActor(actor.Actor):
    async def receive(self, context: context.AbstractContext) -> None:
        message = context.message
        if isinstance(message, HelloMessage):
            print(message.text)


if __name__ == "__main__":
    context = RootContext()
    props = Props.from_producer(lambda: HelloActor())
    pid = context.spawn(props)
    pid.tell(HelloMessage('Hello World!'))
