from protoactor import actor, context


class HelloMessage:
    def __init__(self, text: str):
        self.text = text


class HelloActor(actor.Actor):
    async def receive(self, context: context.AbstractContext) -> None:
        message = context.message
        if isinstance(message, HelloMessage):
            print(message.text)


if __name__ == "__main__":
    props = actor.from_producer(lambda: HelloActor())
    pid = actor.spawn(props)
    pid.tell(HelloMessage('Hello World!'))
    input()
