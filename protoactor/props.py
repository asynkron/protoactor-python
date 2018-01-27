from asyncio import Task
from typing import Callable, List

from . import context, dispatcher, invoker, messages, process, process_registry, supervision
from .mailbox import mailbox, queue
from .protos_pb2 import PID


def default_spawner(id: str, props: 'Props', parent: PID) -> PID:
    _context = context.LocalContext(props.producer, props.supervisor, props.middleware_chain, parent)
    mailbox = props.produce_mailbox(_context, props.dispatcher)
    _process = process.LocalProcess(mailbox)

    pid = process_registry.ProcessRegistry().add(id, _process)
    _context.my_self = pid

    mailbox.start()
    mailbox.post_system_message(messages.Started())

    return pid


def default_mailbox_producer(invoker: invoker.AbstractInvoker, dispatcher: 'AbstractDispatcher'):
    return mailbox.Mailbox(queue.UnboundedMailboxQueue(), queue.UnboundedMailboxQueue(), invoker, dispatcher)


class Props:
    def __init__(self, producer: Callable[[], 'Actor'] = None,
                 spawner: Callable[[str, 'Props', PID], PID] = default_spawner,
                 mailbox_producer: Callable[
                     [invoker.AbstractInvoker,
                      'AbstractDispatcher'], mailbox.AbstractMailbox] = default_mailbox_producer,
                 dispatcher: 'AbstractDispatcher' = dispatcher.ThreadDispatcher(),
                 supervisor_strategy: supervision.AbstractSupervisorStrategy = None,
                 middleware: List[Callable[[context.AbstractContext], Task]] = None,
                 middleware_chain: Callable[[context.AbstractContext], Task] = None) -> None:
        self.__producer = producer
        self.__spawner = spawner
        self.__mailbox_producer = mailbox_producer
        self.__supervisor_strategy = supervisor_strategy
        self.__dispatcher = dispatcher
        self.__middleware = middleware
        self.__middleware_chain = middleware_chain

    @property
    def producer(self) -> Callable[[], 'Actor']:
        return self.__producer

    @property
    def mailbox_producer(self) -> Callable[[invoker.AbstractInvoker, 'AbstractDispatcher'], mailbox.AbstractMailbox]:
        return self.__mailbox_producer

    @property
    def supervisor(self):
        return self.__supervisor_strategy

    @property
    def middleware(self) -> List[Callable[[context.AbstractContext], Task]]:
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

    def with_middleware(self, middleware: List[Callable[[context.AbstractContext], Task]]) -> 'Props':
        return self.__copy_with({'_Props__middleware': middleware})

    def with_mailbox_producer(self, mailbox_producer: Callable[[], mailbox.AbstractMailbox]) -> 'Props':
        return self.__copy_with({'_Props__mailbox_producer': mailbox_producer})

    def with_supervisor_strategy(self, supervisor_strategy) -> 'Props':
        return self.__copy_with({'_Props__supervisor_strategy': supervisor_strategy})

    def spawn(self, id: str, parent: PID = None) -> PID:
        return self.__spawner(id, self, parent)

    def produce_mailbox(self, invoker: invoker.AbstractInvoker,
                        dispatcher: 'AbstractDispatcher') -> mailbox.AbstractMailbox:
        return self.__mailbox_producer(invoker, dispatcher)

    def __copy_with(self, new_params: dict) -> 'Props':
        params = self.__dict__
        params.update(new_params)

        _params = {}
        for key in params:
            new_key = key.replace('_Props__', '')
            _params[new_key] = params[key]

        return Props(**_params)
