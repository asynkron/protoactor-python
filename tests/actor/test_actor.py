import asyncio
import signal
from datetime import timedelta

import pytest

from protoactor.actor.actor import RootContext
from protoactor.actor.props import Props

context = RootContext()


async def hello_function(context):
    message = context.message
    if isinstance(message, str):
        await context.respond("hey")


async def empty_receive(context):
    pass


@pytest.mark.asyncio
async def test_request_actor_async():
    props = Props.from_func(hello_function)
    pid = context.spawn(props)
    reply = await context.request_future(pid, "hello")

    assert reply == "hey"


@pytest.mark.asyncio
async def test_request_actor_async_should_raise_timeout_exception_when_timeout_is_reached():
    with pytest.raises(TimeoutError) as excinfo:
        props = Props.from_func(empty_receive)
        pid = context.spawn(props)
        await context.request_future(pid, "", timedelta(seconds=1))

    assert 'TimeoutError' in str(excinfo)

@pytest.mark.asyncio
async def test_request_actor_async_should_not_raise_timeout_exception_when_result_is_first():
    props = Props.from_func(hello_function)
    pid = context.spawn(props)
    reply = await context.request_future(pid, "hello", timedelta(seconds=1))

    assert reply == "hey"