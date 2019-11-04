import traceback
from collections import Callable
from typing import Optional

from jaeger_client import Tracer, SpanContext, Span
from opentracing.tags import ERROR


class OpenTracingHelper:
    @staticmethod
    def build_started_scope(tracer: Tracer, parent_span: SpanContext, verb: str, message: any,
                            span_setup: 'Callable[[Span, any], None]') -> None:
        message_type = type(message).__name__
        scope = tracer.start_active_span(f'{verb} {message_type}', child_of=parent_span)
        scope.span.set_tag('proto.messagetype', message_type)

        if span_setup is not None:
            span_setup(scope.span, message)

        return scope

    @staticmethod
    def setup_span(exception: Exception, span: Span) -> None:
        if span is None:
            return

        span.set_tag(ERROR, True)
        span.log_kv({'exception': type(exception).__name__,
                     'message': str(exception),
                     'stackTrace': traceback.format_exception(etype=type(exception),
                                                              value=exception,
                                                              tb=exception.__traceback__)})

    @staticmethod
    def get_parent_span(tracer: Tracer) -> Optional[SpanContext]:
        if tracer.active_span is not None:
            return tracer.active_span.context
        return None

    @staticmethod
    def default_setup_span(span: Span, message: any) -> None:
        pass
