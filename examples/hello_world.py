from protoactor.actor.props import Props
from protoactor.actor.actor import Actor, AbstractContext, RootContext


class HelloMessage:
    def __init__(self, text: str):
        self.text = text


class HelloActor(Actor):
    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, HelloMessage):
            print(message.text)


if __name__ == "__main__":
    context = RootContext()
    props = Props.from_producer(HelloActor)
    pid = context.spawn(props)
    pid.tell(HelloMessage('Hello World!'))
