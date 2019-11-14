from typing import Callable

import opentracing
from jaeger_client import Span, Tracer

from protoactor.actor.actor_context import AbstractContext, AbstractRootContext
from protoactor.actor.props import Props
from protoactor.tracing.opentracing.open_tracing_decorator import OpenTracingRootContextDecorator, \
    OpenTracingActorContextDecorator
from protoactor.tracing.opentracing.open_tracing_helper import OpenTracingHelper
from protoactor.tracing.opentracing.open_tracing_middleware import open_tracing_sender_middleware


class OpenTracingFactory:
    @staticmethod
    def get_props_with_open_tracing(props: Props, send_span_setup: Callable[[Span, any], None] = None,
                                    receive_span_setup: Callable[[Span, any], None] = None,
                                    tracer: Tracer = None) -> Props:
        def fn(ctx):
            return OpenTracingFactory.get_context_with_open_tracing(ctx, send_span_setup, receive_span_setup)

        new_props = props.with_context_decorator([fn])
        return OpenTracingFactory.get_props_with_open_tracing_sender(new_props, tracer)

    @staticmethod
    def get_props_with_open_tracing_sender(props: Props, tracer: Tracer) -> Props:
        return props.with_sender_middleware([open_tracing_sender_middleware(tracer)])

    @staticmethod
    def get_context_with_open_tracing(context: AbstractContext, send_span_setup: Callable[[Span, any], None] = None,
                                      receive_span_setup: Callable[[Span, any], None] = None,
                                      tracer: Tracer = None) -> OpenTracingActorContextDecorator:
        if send_span_setup is None:
            send_span_setup = OpenTracingHelper.default_setup_span

        if receive_span_setup is None:
            receive_span_setup = OpenTracingHelper.default_setup_span

        if tracer is None:
            tracer = opentracing.global_tracer()

        return OpenTracingActorContextDecorator(context, send_span_setup, receive_span_setup, tracer)

    @staticmethod
    def get_root_context_with_open_tracing(context: AbstractRootContext,
                                           send_span_setup: Callable[[Span, any], None] = None,
                                           tracer: Tracer = None) -> OpenTracingRootContextDecorator:
        if send_span_setup is None:
            send_span_setup = OpenTracingHelper.default_setup_span

        if tracer is None:
            tracer = opentracing.global_tracer()

        return OpenTracingRootContextDecorator(context, send_span_setup, tracer)
