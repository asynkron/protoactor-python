from asyncio import Task
from typing import Callable, List

from .actor import Actor
from .context import LocalContext, AbstractContext
from .dispatcher import AbstractDispatcher, ProcessDispatcher
from .invoker import AbstractInvoker
from .mailbox.mailbox import AbstractMailbox, Mailbox
from .mailbox.queue import UnboundedMailboxQueue
from .messages import Started
from .pid import PID
from .process import LocalProcess
from .process_registry import ProcessRegistry
from .supervision import AbstractSupervisorStrategy


def default_spawner(id: str, props: 'Props', parent: PID) -> PID:
    context = LocalContext(props.producer, props.supervisor, props.middleware_chain, parent)
    mailbox = props.produce_mailbox(context, props.dispatcher)
    process = LocalProcess(mailbox)

    pid = ProcessRegistry().add(id, process)
    context.my_self = pid

    mailbox.start()
    mailbox.post_system_message(Started())

    return pid


def default_mailbox_producer(invoker: AbstractInvoker, dispatcher: AbstractDispatcher):
    return Mailbox(UnboundedMailboxQueue(), UnboundedMailboxQueue(), invoker, dispatcher)


class Props:
    def __init__(self, producer: Callable[[], Actor] = None,
                 spawner: Callable[[str, 'Props', PID], PID] = default_spawner,
                 mailbox_producer: Callable[
                     [AbstractInvoker, AbstractDispatcher], AbstractMailbox] = default_mailbox_producer,
                 dispatcher: AbstractDispatcher = ProcessDispatcher(),
                 supervisor_strategy: AbstractSupervisorStrategy = None,
                 middleware: List[Callable[[AbstractContext], Task]] = None,
                 middleware_chain: Callable[[AbstractContext], Task] = None) -> None:
        self.__producer = producer
        self.__spawner = spawner
        self.__mailbox_producer = mailbox_producer
        self.__supervisor_strategy = supervisor_strategy
        self.__dispatcher = dispatcher
        self.__middleware = middleware
        self.__middleware_chain = middleware_chain

    @property
    def producer(self) -> Callable[[], Actor]:
        return self.__producer

    @property
    def supervisor(self):
        return self.__supervisor_strategy

    @property
    def middleware_chain(self):
        return self.__middleware_chain

    @property
    def dispatcher(self):
        return self.__dispatcher

    def with_producer(self, producer: Callable[[], Actor]) -> 'Props':
        return self.__copy_with({'_Props__producer': producer})

    def with_dispatcher(self, dispatcher: AbstractDispatcher) -> 'Props':
        return self.__copy_with({'_Props__dispatcher': dispatcher})

    def with_middleware(self, middleware: List[Callable[[AbstractContext], Task]]) -> 'Props':
        return self.__copy_with({'_Props__middleware': middleware})

    def with_mailbox_producer(self, mailbox_producer: Callable[[], AbstractMailbox]) -> 'Props':
        return self.__copy_with({'_Props__mailbox_producer': mailbox_producer})

    def with_supervisor_strategy(self, supervisor_strategy) -> 'Props':
        return self.__copy_with({'_Props__supervisor_strategy': supervisor_strategy})

    def spawn(self, id: str, parent: PID = None) -> PID:
        return self.__spawner(id, self, parent)

    def produce_mailbox(self, invoker: AbstractInvoker, dispatcher: AbstractDispatcher) -> AbstractMailbox:
        return self.__mailbox_producer(invoker, dispatcher)

    def __copy_with(self, new_params: dict) -> 'Props':
        params = self.__dict__
        params.update(new_params)

        return Props(**params)
