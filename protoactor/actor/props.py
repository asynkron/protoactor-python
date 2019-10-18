from asyncio import Task
from functools import reduce
from typing import Callable, List

from protoactor.actor import ProcessRegistry
from protoactor.actor.actor import ActorContext, Actor, EmptyActor, AbstractContext, Started, AbstractReceiverContext, \
    AbstractSenderContext
from protoactor.actor.exceptions import ProcessNameExistException
from protoactor.actor.message_envelope import MessageEnvelope
from protoactor.actor.process import ActorProcess
from protoactor.actor.protos_pb2 import PID
from protoactor.actor.supervision import AbstractSupervisorStrategy, Supervision
from protoactor.mailbox import mailbox
from protoactor.mailbox.dispatcher import AbstractDispatcher, Dispatchers
from protoactor.mailbox.mailbox import MailboxFactory


def default_spawner(name: str, props: 'Props', parent: PID) -> PID:
    _ctx = ActorContext(props, parent)
    _mailbox = props.mailbox_producer()
    _dispatcher = props.dispatcher
    _process = ActorProcess(_mailbox)
    _pid, _absent = ProcessRegistry().try_add(name, _process)
    if not _absent:
        raise ProcessNameExistException(name, _pid)
    _ctx.my_self = _pid
    _mailbox.register_handlers(_ctx, _dispatcher)
    _mailbox.post_system_message(Started())
    _mailbox.start()

    return _pid


def default_context_decorator(context: AbstractContext) -> AbstractContext:
    return context


class Middleware:
    @staticmethod
    async def receive(context: AbstractReceiverContext, envelope: MessageEnvelope) -> None:
        await context.receive(envelope)

    @staticmethod
    async def sender(context: AbstractSenderContext, target: PID, envelope: MessageEnvelope) -> None:
        await target.send_user_message(envelope)


class Props:
    def __init__(self, producer: Callable[[], 'Actor'] = None,
                 spawner: Callable[[str, 'Props', PID], PID] = default_spawner,
                 mailbox_producer: Callable[[], mailbox.AbstractMailbox] =
                 MailboxFactory.create_unbounded_mailbox,
                 guardian_strategy: AbstractSupervisorStrategy = None,
                 supervisor_strategy: AbstractSupervisorStrategy = Supervision.default_strategy,
                 dispatcher: AbstractDispatcher = Dispatchers().default_dispatcher,
                 receive_middleware: List[Callable[[AbstractContext], Task]] = [],
                 sender_middleware: List[Callable[[AbstractContext], Task]] = [],
                 receive_middleware_chain: Callable[[AbstractContext], Task] = None,
                 sender_middleware_chain: Callable[[AbstractContext], Task] = None,
                 context_decorator: List[Callable[[AbstractContext], AbstractContext]] = [],
                 context_decorator_chain: Callable[[AbstractContext], AbstractContext] = default_context_decorator) -> \
            None:
        self.__spawner = spawner
        self.__producer = producer
        self.__mailbox_producer = mailbox_producer
        self.__guardian_strategy = guardian_strategy
        self.__supervisor_strategy = supervisor_strategy
        self.__dispatcher = dispatcher
        self.__receive_middleware = receive_middleware
        self.__sender_middleware = sender_middleware
        self.__receive_middleware_chain = receive_middleware_chain
        self.__sender_middleware_chain = sender_middleware_chain
        self.__context_decorator = context_decorator
        self.__context_decorator_chain = context_decorator_chain

    @property
    def producer(self) -> Callable[[], 'Actor']:
        return self.__producer

    @property
    def mailbox_producer(self) -> Callable[[], mailbox.AbstractMailbox]:
        return self.__mailbox_producer

    @property
    def guardian_strategy(self) -> AbstractSupervisorStrategy:
        return self.__guardian_strategy

    @property
    def supervisor_strategy(self):
        return self.__supervisor_strategy

    @property
    def dispatcher(self):
        return self.__dispatcher

    @property
    def receive_middleware(self) -> List[Callable[[AbstractContext], Task]]:
        return self.__receive_middleware

    @property
    def sender_middleware(self) -> List[Callable[[AbstractContext], Task]]:
        return self.__sender_middleware

    @property
    def receive_middleware_chain(self):
        return self.__receive_middleware_chain

    @property
    def sender_middleware_chain(self):
        return self.__sender_middleware_chain

    @property
    def context_decorator(self):
        return self.__context_decorator

    @property
    def context_decorator_chain(self):
        return self.__context_decorator_chain

    def with_producer(self, producer: Callable[[], 'Actor']) -> 'Props':
        return self.__copy_with({'_Props__producer': producer})

    def with_dispatcher(self, dispatcher: 'AbstractDispatcher') -> 'Props':
        return self.__copy_with({'_Props__dispatcher': dispatcher})

    def with_mailbox(self, mailbox_producer: Callable[..., mailbox.AbstractMailbox]) -> 'Props':
        return self.__copy_with({'_Props__mailbox_producer': mailbox_producer})

    def with_guardian_supervisor_strategy(self, guardian_strategy) -> 'Props':
        return self.__copy_with({'_Props__guardian_strategy': guardian_strategy})

    def with_child_supervisor_strategy(self, supervisor_strategy) -> 'Props':
        return self.__copy_with({'_Props__supervisor_strategy': supervisor_strategy})

    def with_receive_middleware(self, middleware: List[Callable[[AbstractContext], Task]]) -> 'Props':
        new_middleware = self.__get_middleware(self.__receive_middleware, middleware)

        receive_middleware_chain = reduce(lambda inner, outer: outer(inner), new_middleware, Middleware.receive)
        return self.__copy_with({'_Props__receive_middleware': new_middleware,
                                 '_Props__receive_middleware_chain': receive_middleware_chain})

    def with_sender_middleware(self, middleware: List[Callable[[AbstractContext], Task]]) -> 'Props':
        new_middleware = self.__get_middleware(self.__sender_middleware, middleware)

        sender_middleware_chain = reduce(lambda inner, outer: outer(inner), new_middleware, Middleware.sender)
        return self.__copy_with({'_Props__sender_middleware': new_middleware,
                                 '_Props__sender_middleware_chain': sender_middleware_chain})

    def with_spawner(self, spawner) -> 'Props':
        return self.__copy_with({'_Props__spawner': spawner})

    def spawn(self, id: str, parent: PID = None) -> PID:
        return self.__spawner(id, self, parent)

    def __copy_with(self, new_params: dict) -> 'Props':
        params = self.__dict__
        params.update(new_params)

        _params = {}
        for key in params:
            new_key = key.replace('_Props__', '')
            _params[new_key] = params[key]

        return Props(**_params)

    @staticmethod
    def __get_middleware(existing_middleware, new_middleware):
        if existing_middleware is None:
            middleware = existing_middleware
        else:
            middleware = new_middleware + existing_middleware
        return list(reversed(middleware))

    @staticmethod
    def from_producer(producer: Callable[[], Actor]) -> 'Props':
        return Props(producer=producer)

    @staticmethod
    def from_func(receive) -> 'Props':
        return Props.from_producer(lambda: EmptyActor(receive))
