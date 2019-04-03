from asyncio import Task
from typing import Callable, List

from protoactor.actor import PID, ProcessRegistry
from protoactor.actor.actor import ActorContext, Actor, EmptyActor, AbstractContext, Started
from protoactor.actor.exceptions import ProcessNameExistException
from protoactor.actor.process import LocalProcess
from protoactor.actor.supervision import AbstractSupervisorStrategy, Supervision
from protoactor.mailbox import mailbox
from protoactor.mailbox.dispatcher import ThreadDispatcher, AbstractDispatcher
from protoactor.mailbox.mailbox import MailboxFactory


def default_spawner(name: str, props: 'Props', parent: PID) -> PID:
    _ctx = ActorContext(props.producer, props.supervisor_strategy, props.middleware_chain, parent)
    _mailbox = props.mailbox_producer()
    _dispatcher = props.dispatcher
    _process = LocalProcess(_mailbox)
    _pid, _absent = ProcessRegistry().try_add(name, _process)
    if not _absent:
        raise ProcessNameExistException(name, _pid)
    _ctx.my_self = _pid
    _mailbox.register_handlers(_ctx, _dispatcher)
    _mailbox.post_system_message(Started())
    _mailbox.start()

    return _pid

class Props:
    def __init__(self, producer: Callable[[], 'Actor'] = None,
                 spawner: Callable[[str, 'Props', PID], PID] = default_spawner,
                 mailbox_producer: Callable[[], mailbox.AbstractMailbox] =
                 MailboxFactory.create_unbounded_mailbox,
                 guardian_strategy: AbstractSupervisorStrategy = None,
                 dispatcher: AbstractDispatcher = ThreadDispatcher(),
                 middleware: List[Callable[[AbstractContext], Task]] = None,
                 middleware_chain: Callable[[AbstractContext], Task] = None) -> None:
        self.__producer = producer
        self.__spawner = spawner
        self.__mailbox_producer = mailbox_producer
        self.__guardian_strategy = guardian_strategy
        self.__dispatcher = dispatcher
        self.__middleware = middleware
        self.__middleware_chain = middleware_chain

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
        return Supervision().default_strategy

    @property
    def middleware(self) -> List[Callable[[AbstractContext], Task]]:
        return self.__middleware

    @property
    def middleware_chain(self):
        return self.__middleware_chain

    @property
    def dispatcher(self):
        return self.__dispatcher

    def with_producer(self, producer: Callable[[], 'Actor']) -> 'Props':
        return self.__copy_with({'_Props__producer': producer})

    def with_dispatcher(self, dispatcher: 'AbstractDispatcher') -> 'Props':
        return self.__copy_with({'_Props__dispatcher': dispatcher})

    def with_middleware(self, middleware: List[Callable[[AbstractContext], Task]]) -> 'Props':
        return self.__copy_with({'_Props__middleware': middleware})

    def with_mailbox(self, mailbox_producer: Callable[..., mailbox.AbstractMailbox]) -> 'Props':
        return self.__copy_with({'_Props__mailbox_producer': mailbox_producer})

    def with_guardian_supervisor_strategy(self, guardian_strategy) -> 'Props':
        return self.__copy_with({'_Props__guardian_strategy': guardian_strategy})

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
    def from_producer(producer: Callable[[], Actor]) -> 'Props':
        return Props(producer=producer)

    @staticmethod
    def from_func(receive) -> 'Props':
        return Props.from_producer(lambda: EmptyActor(receive))