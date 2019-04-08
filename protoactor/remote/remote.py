import asyncio
import threading
from typing import Dict

from grpclib.client import Channel
from grpclib.const import Status
from grpclib.exceptions import GRPCError, StreamTerminatedError
from grpclib.server import Server

import protoactor.actor.message_envelope as proto
from protoactor.actor import actor
from protoactor.actor.actor import Actor, ProcessRegistry, GlobalRootContext, AbstractContext
from protoactor.actor.behavior import Behavior
from protoactor.actor.event_stream import GlobalEventStream
from protoactor.actor.exceptions import ProcessNameExistException
from protoactor.actor.messages import Stopped, Started, Restarting
from protoactor.actor.process import AbstractProcess, DeadLettersProcess
from protoactor.actor.props import Props
from protoactor.actor.protos_pb2 import Watch, Unwatch, Terminated, PID, Stop
from protoactor.actor.restart_statistics import RestartStatistics
from protoactor.actor.supervision import AbstractSupervisorStrategy, AbstractSupervisor, Supervision
from protoactor.actor.utils import singleton
from protoactor.mailbox.dispatcher import Dispatchers, GlobalSynchronousDispatcher
from protoactor.mailbox.mailbox import AbstractMailbox, MailboxFactory
from protoactor.mailbox.messages import SuspendMailbox, ResumeMailbox
from protoactor.mailbox.queue import UnboundedMailboxQueue
from protoactor.remote.exceptions import ActivatorException
from protoactor.remote.messages import RemoteDeliver, RemoteWatch, RemoteUnwatch, EndpointConnectedEvent, \
    EndpointTerminatedEvent, RemoteTerminate, Endpoint
from protoactor.remote.protos_remote_grpc import RemotingBase, RemotingStub
from protoactor.remote.protos_remote_pb2 import ConnectResponse, Unit, MessageHeader, MessageBatch, ConnectRequest, \
    ActorPidRequest, ActorPidResponse, MessageEnvelope
from protoactor.remote.response import ResponseStatusCode
from protoactor.remote.serialization import Serialization


class RemoteConfig():
    def __init__(self):
        self.endpoint_writer_batch_size = 1000
        self.channel_options = None
        self.call_options = None
        self.channel_credentials = None
        self.server_credentials = None
        self.advertised_hostname = None
        self.advertised_port = None


class Remote(metaclass=singleton):
    def __init__(self):
        self.__logger = None
        self._server = None
        self.__kinds = {}
        self.__remote_config = None
        self.__activator_pid = None
        self._endpoint_reader = None

    @property
    def remote_config(self) -> RemoteConfig:
        return self.__remote_config

    @property
    def get_known_kinds(self) -> list:
        return list(self.__kinds.keys())

    def register_known_kind(self, kind: str, props: Props) -> None:
        self.__kinds[kind] = props

    def get_known_kind(self, kind: str) -> Props:
        props = self.__kinds.get(kind)
        if props is None:
            raise ValueError("save must be True if recurse is True")
        return props

    def start(self, hostname: str, port: int, config: RemoteConfig = RemoteConfig()) -> None:
        self.__remote_config = config
        ProcessRegistry().register_host_resolver(RemoteProcess)
        EndpointManager().start()
        self._endpoint_reader = EndpointReader()

        Dispatchers().default_dispatcher.schedule(self.__run, hostname=hostname, port=port)

        address = "%s:%s" % (hostname, port)
        ProcessRegistry().address = address
        self.__spawn_activator()
        # self.__logger.log_debug('Starting Proto.Actor server on %s (%s)' % (bound_address, address))

    def shutdown(self, gracefull=True):
        try:
            if (gracefull):
                EndpointManager().stop()
                self._endpoint_reader.suspend(True)
                self.__stop_activator()
                self._server.close()
            else:
                self._server.close()
            # self.__logger.log_debug('Proto.Actor server stopped on %s. Graceful:%s' %
            #                         (ProcessRegistry().address, gracefull))
        except Exception as e:
            self._server.close()
            self.__logger.log_debug('Proto.Actor server stopped on %s. with error:%s' %
                                    (ProcessRegistry().address, str(e)))

    def activator_for_address(self, address):
        return PID(address=address, id='activator')

    def spawn_async(self, address, kind, timeout):
        pass

    async def spawn_named_async(self, address, name, kind, timeout):
        activator = self.activator_for_address(address)
        return await GlobalRootContext().instance.request_async(activator, ActorPidRequest(name=name, kind=kind),
                                                                timeout=timeout)

    def send_message(self, pid, msg, serializer_id):
        message, sender, header = actor.MessageEnvelope.unwrap(msg)
        env = RemoteDeliver(header, message, pid, sender, serializer_id)
        EndpointManager().remote_deliver(env)

    def __spawn_activator(self):
        props = Props().from_producer(Activator) \
            .with_guardian_supervisor_strategy(Supervision().always_restart_strategy)
        self.__activator_pid = GlobalRootContext().instance.spawn_named(props, 'activator')

    def __stop_activator(self):
        self.__activator_pid.stop()

    async def __run(self, hostname: str, port: int):
        self._server = Server([self._endpoint_reader], loop=asyncio.get_event_loop())
        await self._server.start(host=hostname, port=port)
        await self._server.wait_closed()


class RemoteProcess(AbstractProcess):
    def __init__(self, pid: 'PID'):
        self._pid = pid

    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None):
        self.send(message)

    def send_system_message(self, pid: 'PID', message: object):
        self.send(message)

    def send(self, message: any):
        if isinstance(message, Watch):
            EndpointManager().remote_watch(RemoteWatch(message.watcher, self._pid))
        elif isinstance(message, Unwatch):
            EndpointManager().remote_unwatch(RemoteUnwatch(message.watcher, self._pid))
        else:
            Remote().send_message(self._pid, message, -1)


class EndpointManager(metaclass=singleton):
    def __init__(self):
        self._logger = None
        self._connections = {}
        self._endpoint_supervisor = None
        self._endpoint_term_evn_sub = None
        self._endpoint_conn_evn_sub = None

    def start(self) -> None:
        # self.__logger.log_debug('Started EndpointManager')
        props = Props().from_producer(EndpointSupervisor) \
            .with_guardian_supervisor_strategy(Supervision().always_restart_strategy) \
            .with_dispatcher(Dispatchers().synchronous_dispatcher) \
            .with_mailbox(MailboxFactory().create_unbounded_synchronous_mailbox)

        self._endpoint_supervisor = GlobalRootContext().instance.spawn_named(props, 'EndpointSupervisor')
        self._endpoint_conn_evn_sub = GlobalEventStream().instance.subscribe(self.__on_endpoint_connected,
                                                                             EndpointConnectedEvent)
        self._endpoint_term_evn_sub = GlobalEventStream().instance.subscribe(self.__on_endpoint_terminated,
                                                                             EndpointTerminatedEvent)

    def stop(self) -> None:
        self._endpoint_conn_evn_sub.unsubscribe()
        self._endpoint_term_evn_sub.unsubscribe()
        self._connections.clear()

        self._endpoint_supervisor.stop()
        # self.__logger.log_debug('Stopped EndpointManager')

    def remote_watch(self, msg: RemoteWatch) -> None:
        endpoint = self.__ensure_connected(msg.watchee.address)
        GlobalRootContext().instance.send(endpoint.watcher, msg)

    def remote_unwatch(self, msg: RemoteUnwatch) -> None:
        endpoint = self.__ensure_connected(msg.watchee.address)
        GlobalRootContext().instance.send(endpoint.watcher, msg)

    def remote_deliver(self, msg: RemoteDeliver) -> None:
        endpoint = self.__ensure_connected(msg.target.address)
        GlobalRootContext().instance.send(endpoint.writer, msg)

    def remote_terminate(self, msg: RemoteTerminate):
        endpoint = self.__ensure_connected(msg.watchee.address)
        GlobalRootContext().instance.send(endpoint.watcher, msg)

    async def __on_endpoint_connected(self, msg: EndpointConnectedEvent) -> None:
        endpoint = self.__ensure_connected(msg.address)
        GlobalRootContext().instance.send(endpoint.watcher, msg)

    async def __on_endpoint_terminated(self, msg: EndpointTerminatedEvent) -> None:
        endpoint = self._connections.get(msg.address)
        if endpoint is not None:
            GlobalRootContext().instance.send(endpoint.watcher, msg)
            GlobalRootContext().instance.send(endpoint.writer, msg)
            del self._connections[msg.address]

    def __ensure_connected(self, address) -> Endpoint:
        endpoint = self._connections.get(address)
        if endpoint is None:
            async def test():
                return await GlobalRootContext().instance.request_async(self._endpoint_supervisor, address)

            endpoint = GlobalSynchronousDispatcher().schedule(test)
            self._connections[address] = endpoint
        return endpoint


class EndpointReader(RemotingBase):
    def __init__(self):
        self.__suspended = False

    async def Connect(self, stream):
        if self.__suspended:
            raise GRPCError(Status.CANCELLED, "Suspended")
        await stream.send_message(ConnectResponse(default_serializer_id=Serialization().default_serializer_id))

    async def Receive(self, stream) -> None:
        targets = []
        async for batch in stream:
            if self.__suspended:
                await stream.send_message(Unit())

            for i in range(len(batch.target_names)):
                targets.append(PID(address=ProcessRegistry().address, id=batch.target_names[i]))

            type_names = list(batch.type_names)
            for envelope in batch.envelopes:
                target = targets[envelope.target]
                type_name = type_names[envelope.type_id]
                message = Serialization().deserialize(type_name, envelope.message_data, envelope.serializer_id)

                if isinstance(message, Terminated):
                    EndpointManager().remote_terminate(RemoteTerminate(target, message.who))
                elif isinstance(message, Watch):
                    target.send_system_message(message)
                elif isinstance(message, Unwatch):
                    target.send_system_message(message)
                elif isinstance(message, Stop):
                    target.send_system_message(message)
                else:
                    header = None
                    if envelope.message_header is not None:
                        header = proto.MessageHeader(envelope.message_header.header_data)
                    local_envelope = proto.MessageEnvelope(message, envelope.sender, header)
                    GlobalRootContext().instance.send(target, local_envelope)

        await stream.send_message(Unit())

    def suspend(self, suspended) -> None:
        self.__suspended = suspended


class EndpointWatcher(Actor):
    def __init__(self, address):
        self.__address = address
        self.__behavior = Behavior(self.connected)
        self.__logger = None
        self._watched = {}

    async def receive(self, context: AbstractContext) -> None:
        await self.__behavior.receive_async(context)

    async def connected(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, RemoteTerminate):
            self.__process_remote_terminate_message_in_connected_state(message)
        elif isinstance(message, EndpointTerminatedEvent):
            self.__process_endpoint_terminated_event_message_in_connected_state(context, message)
        elif isinstance(message, RemoteUnwatch):
            self.__process_remote_unwatch_message_in_connected_state(message)
        elif isinstance(message, RemoteWatch):
            self.__process_remote_watch_message_in_connected_state(message)
        elif isinstance(message, Stopped):
            self.__process_stopped_message_in_connected_state()

    async def terminated(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, RemoteWatch):
            self.__process_remote_watch_message_in_terminated_state(message)
        elif isinstance(message, EndpointConnectedEvent):
            self.__process_endpoint_connected_event_message_in_terminated_state()

    def __process_remote_terminate_message_in_connected_state(self, msg):
        if msg.watcher.id in self._watched:
            pid_set = self._watched[msg.watcher.id]
            pid_set.remove(msg.watchee)
            if len(pid_set) == 0:
                del self._watched[msg.watcher.id]

        msg.watcher.send_system_message(Terminated(who=msg.watchee))

    def __process_endpoint_terminated_event_message_in_connected_state(self, context, msg):
        # self.__logger.log_debug()
        for watched_id, pid_set in self._watched.items():
            watcher_pid = PID(address=ProcessRegistry().address, id=watched_id)
            watcher_ref = ProcessRegistry().get(watcher_pid)
            if watcher_ref != DeadLettersProcess():
                for pid in pid_set:
                    watcher_pid.send_system_message(Terminated(who=pid, address_terminated=True))

        self._watched.clear()
        self.__behavior.become(self.terminated)

        context.my_self.stop()

    def __process_remote_unwatch_message_in_connected_state(self, msg):
        if msg.watcher.id in self._watched:
            pid_set = self._watched[msg.watcher.id]
            pid_set.remove(msg.watchee)
            if len(pid_set) == 0:
                del self._watched[msg.watcher.id]

        Remote().send_message(msg.watchee, Unwatch(watcher=msg.watcher), -1)

    def __process_remote_watch_message_in_connected_state(self, msg):
        if msg.watcher.id in self._watched:
            self._watched[msg.watcher.id].append(msg.watchee)
        else:
            self._watched[msg.watcher.id] = [msg.watchee]

        Remote().send_message(msg.watchee, Watch(watcher=msg.watcher), -1)

    def __process_stopped_message_in_connected_state(self):
        self.__logger.log_debug("")

    def __process_remote_watch_message_in_terminated_state(self, msg):
        msg.watcher.send_system_message(Terminated(address_terminated=True, who=msg.watchee))

    def __process_endpoint_connected_event_message_in_terminated_state(self):
        self.__logger.log_debug("")
        self.__behavior.become(self.connected)


class EndpointWriter(Actor):
    def __init__(self, address: str, channel_options: Dict[str, str], call_options,
                 channel_credentials: grpc.ChannelCredentials):
        self._serializer_id = None
        self._logger = None
        self._client = None
        self._channel = None
        self._address = address
        self._channel_options = channel_options
        self._call_options = call_options
        self._channel_credentials = channel_credentials
        self._stream = None
        self._stream_writer = None

    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, Started):
            await self.__started_async()
        elif isinstance(message, Stopped):
            await self.__stopped_async()
        elif isinstance(message, Restarting):
            await self.__restarting_async()
        elif isinstance(message, EndpointTerminatedEvent):
            context.my_self.stop()
        elif isinstance(message, list) and all(isinstance(x, RemoteDeliver) for x in message):
            envelopes = []
            type_names = {}
            target_names = {}
            type_name_list = []
            target_name_list = []

            for rd in message:
                target_name = rd.target.id
                if rd.serializer_id == -1:
                    serializer_id = self._serializer_id
                else:
                    serializer_id = rd.serializer_id

                if target_name not in target_names:
                    target_id = target_names[target_name] = len(target_names)
                    target_name_list.append(target_name)
                else:
                    target_id = target_names[target_name]

                type_name = Serialization().get_type_name(rd.message, serializer_id)
                if type_name not in type_names:
                    type_id = type_names[type_name] = len(type_names)
                    type_name_list.append(type_name)
                else:
                    type_id = type_names[type_name]

                header = None
                if rd.header is not None and rd.header.count > 0:
                    header = MessageHeader(header_data=rd.header)

                message_data = Serialization().serialize(rd.message, serializer_id)

                envelope = MessageEnvelope(type_id=type_id,
                                           message_data=message_data,
                                           target=target_id,
                                           sender=rd.sender,
                                           serializer_id=serializer_id,
                                           message_header=header)

                envelopes.append(envelope)

            batch = MessageBatch()
            batch.target_names.extend(target_name_list)
            batch.type_names.extend(type_name_list)
            batch.envelopes.extend(envelopes)

            await self.__send_envelopes_async(batch, context)

    async def __started_async(self):
        # self.__logger.log_debug("Connecting to address {_address}")
        host, port = self._address.split(':')
        try:
            self._channel = Channel(host=host, port=port, loop=asyncio.get_event_loop())
            self._client = RemotingStub(self._channel)
            res = await self._client.Connect(ConnectRequest())
            self._serializer_id = res.default_serializer_id
        except Exception:
            # self.__logger.log_error("GRPC Failed to connect to address {_address}\n{ex}")
            await asyncio.sleep(2000)
            raise Exception()

        GlobalEventStream().instance.publish(EndpointConnectedEvent(self._address))
        # self.__logger.log_debug("")

    async def __stopped_async(self):
        self._channel.close()
        self._logger.log_debug("")

    async def __restarting_async(self):
        self._channel.close()

    async def __send_envelopes_async(self, batch, context):
        try:
            await self._client.Receive([batch])
        except StreamTerminatedError:
            GlobalEventStream().instance.publish(EndpointTerminatedEvent(self._address))


class EndpointWriterMailbox(AbstractMailbox):
    def __init__(self, batch_size):
        self.__batch_size = batch_size
        self.__system_messages = UnboundedMailboxQueue()
        self.__user_messages = UnboundedMailboxQueue()
        self._dispatcher = None
        self._invoker = None
        self.__event = threading.Event()
        self.__suspended = False

    def post_user_message(self, msg):
        self.__user_messages.push(msg)
        self.__schedule()

    def post_system_message(self, msg):
        self.__system_messages.push(msg)
        self.__schedule()

    def register_handlers(self, invoker, dispatcher):
        self._invoker = invoker
        self._dispatcher = dispatcher
        self._dispatcher.schedule(self.__run)

    def start(self):
        pass

    async def __run(self):
        while True:
            self.__event.wait()
            await self.__process_messages()
            self.__event.clear()

            if self.__system_messages.has_messages() or self.__user_messages.has_messages():
                self.__schedule()

    def __schedule(self):
        self.__event.set()

    async def __process_messages(self):
        message = None
        try:
            batch = []
            sys = self.__system_messages.pop()
            if sys is not None:
                if isinstance(sys, SuspendMailbox):
                    self.__suspended = True
                elif isinstance(sys, ResumeMailbox):
                    self.__suspended = False
                else:
                    message = sys
                    await self._invoker.invoke_system_message(sys)

            if not self.__suspended:
                batch.clear()

                while True:
                    msg = self.__user_messages.pop()
                    if msg is not None or self.__batch_size <= len(batch):
                        batch.append(msg)
                    else:
                        break

                if len(batch) > 0:
                    message = batch
                    await self._invoker.invoke_user_message(batch)
        except Exception as e:
            self._invoker.escalate_failure(e, message)


class EndpointSupervisor(Actor, AbstractSupervisorStrategy):
    def handle_failure(self, supervisor: AbstractSupervisor, child: PID, rs: RestartStatistics, cause: Exception):
        supervisor.restart_children(cause, child)

    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, str):
            address = str(message)
            watcher = self.__spawn_watcher(address, context)
            writer = self.__spawn_writer(address, context)
            context.respond(Endpoint(watcher, writer))

    def __spawn_watcher(self, address: str, context: AbstractContext) -> PID:
        watcher_props = Props.from_producer(lambda: EndpointWatcher(address))
        watcher = context.spawn(watcher_props)
        return watcher

    def __spawn_writer(self, address: str, context: AbstractContext) -> PID:
        writer_props = Props.from_producer(lambda: EndpointWriter(address,
                                                                  Remote().remote_config.channel_options,
                                                                  Remote().remote_config.call_options,
                                                                  Remote().remote_config.channel_credentials))

        writer_props = writer_props.with_mailbox(lambda: EndpointWriterMailbox(Remote()
                                                                               .remote_config
                                                                               .endpoint_writer_batch_size))
        writer = context.spawn(writer_props)
        return writer


class Activator(Actor):
    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, ActorPidRequest):
            props = Remote().get_known_kind(message.kind)
            name = message.name
            if name is None:
                name = ProcessRegistry().next_id()
            try:
                pid = GlobalRootContext().instance.spawn_named(props, name)
                response = ActorPidResponse(pid=pid)
                context.respond(response)
            except ProcessNameExistException as ex:
                response = ActorPidResponse(pid=ex.pid, status_code=int(ResponseStatusCode.ProcessNameAlreadyExist))
                context.respond(response)
            except ActivatorException as ex:
                response = ActorPidResponse(status_code=ex.code)
                context.respond(response)
                if not ex.do_not_throw:
                    raise Exception()
            except Exception:
                response = ActorPidResponse(status_code=int(ResponseStatusCode.Error))
                context.respond(response)
                raise Exception()
