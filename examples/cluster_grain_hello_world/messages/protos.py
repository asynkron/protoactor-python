from abc import ABCMeta, abstractmethod
from datetime import timedelta

from examples.cluster_grain_hello_world.messages.protos_pb2 import HelloRequest, HelloResponse
from protoactor.actor.actor_context import Actor, AbstractContext, RootContext, GlobalRootContext
from protoactor.actor.cancel_token import CancelToken
from protoactor.actor.messages import Started, ReceiveTimeout
from protoactor.actor.props import Props
from protoactor.remote.remote import Remote
from protoactor.remote.response import ResponseStatusCode
from protoactor.cluster.grain_call_options import GrainCallOptions
from protoactor.cluster.protos_pb2 import GrainRequest, GrainResponse, GrainErrorResponse
from protoactor.cluster.сluster import Cluster


class AbstractHelloGrain(metaclass=ABCMeta):
    @abstractmethod
    def say_hello(self, request: HelloRequest) -> HelloResponse:
        raise NotImplementedError('Should implement this method')


class HelloGrainClient():
    def __init__(self, grain_id: str):
        self._grain_id = grain_id

    
    async def say_hello(self, request: HelloRequest, ct: CancelToken = None,
                        options: GrainCallOptions = None) -> HelloResponse:
        if options is None:
            options = GrainCallOptions()

        grain_request = GrainRequest(method_index=0,
                                     message_data=request.SerializeToString())

        async def inner() -> HelloResponse:
            # resolve the grain
            pid, status_code = await Cluster.get_async(self._grain_id, 'HelloGrain', ct)
            if status_code != ResponseStatusCode.OK:
                raise Exception(f'Get PID failed with StatusCode: {status_code}')

            # request the RPC method to be invoked
            grain_response = await GlobalRootContext.request_future(pid, grain_request, ct)

            # did we get a response
            if isinstance(grain_response, GrainResponse):
                response = HelloResponse()
                response.ParseFromString(grain_response.message_data)
                return response

            # did we get an error response
            if isinstance(grain_response, GrainErrorResponse):
                raise Exception(grain_response.err)
            raise AttributeError()

        for i in range(options.retry_count):
            try:
                return await inner()
            except Exception:
                if options.retry_action is not None:
                    await options.retry_action(i)
        return await inner()
    

class HelloGrainActor(Actor):
    def __init__(self):
        self._inner = None

    async def receive(self, context: AbstractContext) -> None:
        message = context.message
        if isinstance(message, Started):
            self._inner = Grains._hello_grain_factory
            context.set_receive_timeout(timedelta(seconds=30))
        elif isinstance(message, ReceiveTimeout):
            await context.my_self.stop()
        elif isinstance(message, GrainRequest):
            if message.method_index == 0:
                request = HelloRequest()
                request.ParseFromString(message.message_data)
                try:
                    response = await self._inner.say_hello(request)
                    grain_response = GrainResponse(message_data=response.SerializeToString())
                    await context.respond(grain_response)
                except Exception as ex:
                    grain_error_response = GrainErrorResponse(err=str(ex))
                    await context.respond(grain_error_response)


class Grains():
    def __init__(self):
        self._hello_grain_factory = None

    def hello_grain_factory(self, factory: AbstractHelloGrain) -> None:
        self._hello_grain_factory = factory
        Remote().register_known_kind('HelloGrain', Props().from_producer(lambda: HelloGrainActor()))

    def hello_grain(self, grain_id: str) -> HelloGrainClient:
        return HelloGrainClient(grain_id)

Grains = Grains()



