from protoactor.actor import Actor, from_producer
from protoactor.pid import PID
from protoactor.context import AbstractContext
from protoactor.messages import Started, Terminated
from protoactor.process_registry import ProcessRegistry
from process import AbstractProcess


class Endpoint:
    def __init__(self, writer: PID, watcher: PID):
        self.writer = writer
        self.watcher = watcher


class EndpointTerminatedEvent:
    def __init__(self, address):
        self.address = address


class RemoteTerminate:
    def __init__(self, writer: PID, watcher: PID):
        self.writer = writer
        self.watcher = watcher


class RemoteWatch:
    def __init__(self, writer: PID, watchee: PID):
        self.writer = writer
        self.watchee = watchee


class RemoteUnwatch:
    def __init__(self, writer: PID, watchee: PID):
        self.writer = writer
        self.watchee = watchee


class RemoteDeliver:
    def __init__(self, message, target: PID, sender: PID):
        self.message = message
        self.target = target
        self.sender = sender


class EndpointManager(Actor):
    def __init__(self):
        self.__connections = {}

    async def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if isinstance(msg, Started):
            # TODO: console log [REMOTING] Started EndpointManager
            return None

        if isinstance(msg, EndpointTerminatedEvent):
            endpoint = self.__ensure_connected(msg.address, context)
            endpoint.watcher.tell(context.message)
            return None

        if isinstance(msg, RemoteTerminate):
            endpoint = self.__ensure_connected(msg.watcher.address, context)
            endpoint.watcher.tell(msg)
            return None

        if isinstance(msg, RemoteWatch):
            endpoint = self.__ensure_connected(msg.watchee.address, context)
            endpoint.watcher.tell(msg)
            return None

        if isinstance(msg, RemoteUnwatch):
            endpoint = self.__ensure_connected(msg.watchee.address, context)
            endpoint.watcher.tell(msg)
            return None

        if isinstance(msg, RemoteDeliver):
            endpoint = self.__ensure_connected(msg.target.address, context)
            endpoint.writer.tell(msg)
            return None

        return None

    def __ensure_connected(self, address, context) -> Endpoint:
        endpoint = self.__connections.get(address, None)
        if endpoint is None:
            writer = self.spawn_writer(address, context)
            watcher = self.__spawn_watcher(address, context)
            endpoint = Endpoint(writer, watcher)
            self.__connections[address] = endpoint
        return endpoint

    def __spawn_watcher(self, address, context) -> PID:
        watcher_props = from_producer(lambda: EndpointWatcher(address))
        watcher = context.spawn(watcher_props)
        return watcher

    def __spawn_witer(self, address, context) -> PID:
        writer_props = from_producer(lambda: EndpointWatcher(address))\
            .with_mailbox_producer(lambda: EndpointWriterMailbox())
        writer = context.spawn(writer_props)
        return writer


class EndpointWatcher(Actor):
    def __init__(self, address):
        self.__address = address
        self.__watched = {}
        self.__watcher = {}

    def receive(self, context: AbstractContext) -> None:
        msg = context.message
        if isinstance(msg, RemoteTerminate):
            self.__watched.pop(msg.watcher.id, 'None')
            self.__watcher.pop(msg.watchee.id, 'None')
            t = Terminated(who=msg.watchee, address_terminated=True)
            msg.watcher.send_system_message(t)

            return None

        if isinstance(msg, EndpointTerminatedEvent):
            for id, pid in self.__watched.items():
                t = Terminated(who=pid, address_terminated=True)
                watcher = PID(ProcessRegistry().Address, id, None)
                watcher.send_system_message(t)

            return None

        if isinstance(msg, RemoteUnwatch):
            self.__watched[msg.watcher.id] = None
            self.__watcher[msg.watchee.id] = None

            w = Unwatch(msg.watcher)
            msg.watchee.send_system_message(w)

            return None

        if isinstance(msg, RemoteWatch):
            self.__watched[msg.watcher.id] = msg.watchee
            self.__watcher[msg.watchee.id] = msg.watcher

            w = Watch(msg.watcher)
            msg.watchee.send_system_message(w)

            return None

        return None


def send_remote_message(pid: 'PID', message: object, sender: 'PID'):
    #TODO: implement this.
    pass


class RemoteProcess (AbstractProcess):
    def __init__(self, pid: 'PID'):
        self.__pid = pid

    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        self.send(pid, message, sender)

    def send_system_message(self, pid: 'PID', message: object):
        self.send(pid, message, None)

    def send(self, pid: 'PID', message: object, sender: 'PID'):
        if isinstance(Watch, message):
            rw = RemoteWatch(message.watcher, self.__pid)
            # endpoint_manager_pid.tell(rw);
        elif isinstance(Unwatch, message):
            ruw = RemoteUnwatch(message.watcher, self.__pid)
            # endpoint_manager_pid.tell(ruw);
        else:
            send_remote_message(self.__pid, message, sender)


class EndpointWriterMailbox:
    # TODO: Implement
    pass

class Unwatch:
    # TODO: Implement
    pass

class Watch:
    # TODO: Implement
    pass
