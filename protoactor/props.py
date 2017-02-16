from typing import Callable

from .dispatcher import AbstractDispatcher, ProcessDispatcher
from .actor import Actor
from .context import AbstractContext
from .mailbox.mailbox import AbstractMailbox, Mailbox
from .mailbox.queue import UnboundedMailboxQueue
from .messages import Started
from .pid import PID
from .process import LocalProcess
from .process_registry import ProcessRegistry


def default_spawner(id: str, props: 'Props', parent: PID) -> PID:
    context = AbstractContext()
    mailbox = props.produce_mailbox()
    process = LocalProcess(mailbox)

    pid = ProcessRegistry().add(id, process)
    context.self = pid

    mailbox.register_handlers(process, props.dispatcher)
    mailbox.post_system_message(Started())
    mailbox.start()
    return pid


def default_mailbox_producer():
    return Mailbox(UnboundedMailboxQueue(), UnboundedMailboxQueue())


class Props:
    def __init__(self, producer: Callable[[], Actor] = None,
                 spawner: Callable[[str, 'Props', PID], PID] = default_spawner,
                 mailbox_producer: Callable[[], AbstractMailbox] = default_mailbox_producer,
                 dispatcher: AbstractDispatcher = ProcessDispatcher()):
        self.__producer = producer
        self.__spawner = spawner
        self.__mailbox_producer = mailbox_producer
        # self.__supervisor_strategy = kwargs.get('supervisor_strategy', None)
        self.__dispatcher = dispatcher
        # self.__middleware = kwargs.get('middleware', [])
        # self.__middleware_chain = kwargs.get('middleware_chain', None)

    @property
    def dispatcher(self):
        return self.__dispatcher

    def with_producer(self, producer: Callable[[], Actor]) -> 'Props':
        pass

    def with_dispatcher(self, producer: Callable[[], Actor]) -> 'Props':
        pass

    def with_middleware(self, *params: Callable[[Actor], Actor]) -> 'Props':
        pass

    def with_mailbox(self, *params: Callable[[Actor], Actor]) -> 'Props':
        pass

    def spawn(self, id: str, parent: PID = None) -> PID:
        return self.__spawner(id, self, parent)

    def produce_mailbox(self) -> AbstractMailbox:
        return self.__mailbox_producer()
