from messages import Started
from context import get_default_receive

def get_default_spawner(name, props, parent):
    ctx = Context(props.producer, props.supervisor_strategy, props.middleware_chain, parent)
    mailbox = props.mailbox_producer
    dispatcher = props.dispatcher
    reff = LocalProcess(mailbox)
    pr = ProcessRegistry().add(name, reff)
    ctx.self = pid

    mailbox.register_handlers(ctx, dispatcher)
    mailbox.post_system_message(Started())
    mailbox.start()

    return pid

def middleware_chain_concat(middleware):
    rv_list = list(reverse(middleware))
    receieve = get_default_receive()
    for m in rv_list:
        receieve = m(receieve)
    
    return receieve

class Props(object):
    def __init__(self, *args, **kwargs):
        self.__producer = kwargs.get('producer', None)
        self.__mailbox_producer = kwargs.get('mailbox_producer', None)
        self.__supervisor_strategy = kwargs.get('supervisor_strategy', None)
        self.__dispatcher = kwargs.get('dispatcher', None)
        self.__middleware = kwargs.get('middleware', [])
        self.__middleware_chain = kwargs.get('middleware_chain', None)
        self.__spawner = kwargs.get('spawner', None)
    
    def __get_spawner(self):
        return self.__spawner if self.__spawner is not None else get_default_spawner

    def __set_spawner(self, val):
        self.__spawner = val

    spawner = property(__get_spawner, __set_spawner)

    @property
    def producer(self):
        return self.__producer
    
    @property
    def mailbox_producer(self):
        return self.__mailbox_producer

    @property
    def supervisor_strategy(self):
        return self.__supervisor_strategy

    @property
    def dispatcher(self):
        return self.__dispatcher

    @property
    def middleware(self):
        return self.__middleware

    @property
    def middleware_chain(self):
        return self.__middleware_chain

    def with_producer(self, producer):
        return self.copy_with({'producer': producer})

    def with_dispatcher(self, dispatcher):
        return self.copy_with({'dispatcher': dispatcher})

    def with_mailbox(self, mailbox):
        return self.copy_with({'mailbox_producer': mailbox})

    def with_supervisor(self, supervisor):
        return self.copy_with({'supervisor_strategy': supervisor})

    def with_middleware(self, middleware):
        new_middleware = self.__middleware.extend(middleware)
        return self.copy_with({
            'middleware': new_middleware,
            'middleware_chain': middleware_chain_concat(new_middleware)
        })

    def with_spawner(self, spawner):
        return self.copy_with({'spawner': spawner})

    def copy_with(self, new_params):
        params = {
            'producer': self.__producer,
            'mailbox_producer': self.mailbox_producer,
            'supervisor_strategy': self.__supervisor_strategy,
            'dispatcher': self.__dispatcher,
            'middleware': self.__middleware,
            'middleware_chain': self.__middleware_chain,
            'spawner': self.__spawner
        }
        params.update(new_params)

        return Props(**params)
