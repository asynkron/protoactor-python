import asyncio
from datetime import timedelta
from typing import Callable

from jaeger_client import Tracer, Span
from opentracing import Format

from protoactor.actor import PID
from protoactor.actor.actor_context import AbstractRootContext, AbstractContext
from protoactor.actor.cancel_token import CancelToken
from protoactor.actor.context_decorator import RootContextDecorator, ActorContextDecorator
from protoactor.actor.message_envelope import MessageEnvelope
from protoactor.tracing.opentracing.open_tracing_helper import OpenTracingHelper


class OpenTracingRootContextDecorator(RootContextDecorator):
    def __init__(self, context: AbstractRootContext,
                 send_span_setup: Callable[[Span, any], None],
                 tracer: Tracer):

        def __send_span_setup(span, message):
            span.set_tag('proto.actortype', '<None>')
            send_span_setup(span, message)

        super().__init__(context)
        self._send_span_setup = __send_span_setup
        self._tracer = tracer

    async def send(self, target: PID, message: any) -> None:
        with OpenTracingHelper.build_started_scope(self._tracer, OpenTracingHelper.get_parent_span(self._tracer),
                                                   'send', message, self._send_span_setup) as scope:
            try:
                scope.span.set_tag('proto.targetpid', target.to_short_string())
                await super().send(target, message)
            except Exception as ex:
                OpenTracingHelper.setup_span(ex, scope.span)
                raise Exception()

    async def request(self, target: PID, message: any) -> None:
        with OpenTracingHelper.build_started_scope(self._tracer, OpenTracingHelper.get_parent_span(self._tracer),
                                                   'request', message, self._send_span_setup) as scope:
            try:
                scope.span.set_tag('proto.targetpid', target.to_short_string())
                await super().request(target, message)
            except Exception as ex:
                OpenTracingHelper.setup_span(ex, scope.span)
                raise Exception()

    async def request_future(self, target: PID, message: object, timeout: timedelta = None,
                             cancellation_token: CancelToken = None) -> asyncio.Future:
        with OpenTracingHelper.build_started_scope(self._tracer, OpenTracingHelper.get_parent_span(self._tracer),
                                                   'request_future', message, self._send_span_setup) as scope:
            try:
                scope.span.set_tag('proto.targetpid', target.to_short_string())
                return await super().request_future(target, message, timeout, cancellation_token)
            except Exception as ex:
                OpenTracingHelper.setup_span(ex, scope.span)
                raise Exception()


class OpenTracingActorContextDecorator(ActorContextDecorator):
    def __init__(self, context: AbstractContext,
                 send_span_setup: Callable[[Span, any], None],
                 receive_span_setup: Callable[[Span, any], None],
                 tracer: Tracer):

        def __send_span_setup(span, message):
            span.set_tag('proto.actortype', type(context.actor).__name__)
            span.set_tag('proto.senderpid', context.my_self.to_short_string())
            send_span_setup(span, message)

        def __receive_span_setup(span, message):
            span.set_tag('proto.actortype', type(context.actor).__name__)
            span.set_tag('proto.targetpid', context.my_self.to_short_string())
            receive_span_setup(span, message)

        super().__init__(context)
        self._send_span_setup = __send_span_setup
        self._receive_span_setup = __receive_span_setup
        self._tracer = tracer

    async def send(self, target: PID, message: any) -> None:
        with OpenTracingHelper.build_started_scope(self._tracer, OpenTracingHelper.get_parent_span(self._tracer),
                                                   'send', message, self._send_span_setup) as scope:
            try:
                scope.span.set_tag('proto.targetpid', target.to_short_string())
                await super().send(target, message)
            except Exception as ex:
                OpenTracingHelper.setup_span(ex, scope.span)
                raise Exception()

    async def request(self, target: PID, message: any) -> None:
        with OpenTracingHelper.build_started_scope(self._tracer, OpenTracingHelper.get_parent_span(self._tracer),
                                                   'request', message, self._send_span_setup) as scope:
            try:
                scope.span.set_tag('proto.targetpid', target.to_short_string())
                await super().request(target, message)
            except Exception as ex:
                OpenTracingHelper.setup_span(ex, scope.span)
                raise Exception()

    async def request_future(self, target: PID, message: object, timeout: timedelta = None,
                             cancellation_token: CancelToken = None) -> asyncio.Future:
        with OpenTracingHelper.build_started_scope(self._tracer, OpenTracingHelper.get_parent_span(self._tracer),
                                                   'request_future', message, self._send_span_setup) as scope:
            try:
                scope.span.set_tag('proto.targetpid', target.to_short_string())
                return await super().request_future(target, message, timeout, cancellation_token)
            except Exception as ex:
                OpenTracingHelper.setup_span(ex, scope.span)
                raise Exception()

    async def forward(self, target: PID) -> None:
        with OpenTracingHelper.build_started_scope(self._tracer, OpenTracingHelper.get_parent_span(self._tracer),
                                                   'forward', super().message, self._send_span_setup) as scope:
            try:
                scope.span.set_tag('proto.targetpid', target.to_short_string())
                await super().forward(target)
            except Exception as ex:
                OpenTracingHelper.setup_span(ex, scope.span)
                raise Exception()

    async def receive(self, envelope: MessageEnvelope) -> None:
        message = envelope.message
        parent_span_ctx = None
        if envelope.header is not None:
            parent_span_ctx = self._tracer.extract(format=Format.TEXT_MAP, carrier=envelope.header)

        with OpenTracingHelper.build_started_scope(self._tracer, parent_span_ctx, 'receive', message,
                                                   self._receive_span_setup) as scope:
            try:
                if envelope.sender is not None:
                    scope.span.set_tag('proto.senderpid', envelope.sender.to_short_string())
                if self._receive_span_setup is not None:
                    self._receive_span_setup(scope.span, message)
                await super().receive(envelope)
            except Exception as ex:
                OpenTracingHelper.setup_span(ex, scope.span)
                raise Exception()
