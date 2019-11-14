import opentracing
from jaeger_client import Tracer
from opentracing import Format

from protoactor.actor import PID
from protoactor.actor.actor_context import AbstractSenderContext
from protoactor.actor.message_envelope import MessageEnvelope


def open_tracing_sender_middleware(tracer: Tracer = None):
    def level_0(next):
        async def level_1(context: AbstractSenderContext, target: PID, envelope: MessageEnvelope):
            if tracer is None:
                inner_tracer = opentracing.global_tracer()
            else:
                inner_tracer = tracer
            span = inner_tracer.active_span
            if span is None:
                await next(context, target, envelope)
            else:
                dictionary = {}
                inner_tracer.inject(span.context, Format.TEXT_MAP, dictionary)
                envelope = envelope.with_headers(dictionary)
                await next(context, target, envelope)

        return level_1

    return level_0
