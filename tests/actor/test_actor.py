import pytest

from protoactor.actor.actor import RootContext
from protoactor.actor.props import Props

context = RootContext()


async def hello_function(context):
    message = context.message
    if isinstance(message, str):
        context.respond("hey")


async def empty_receive(context):
    pass


@pytest.mark.asyncio
async def test_request_actor_async():
    props = Props.from_func(hello_function)
    pid = context.spawn(props)
    reply = await context.request_async(pid, "hello")

    assert "hey" == reply


@pytest.mark.asyncio
async def test_request_actor_async_should_raise_timeout_exception_when_timeout_is_reached():
    with pytest.raises(TimeoutError) as excinfo:
        props = Props.from_func(empty_receive)
        pid = context.spawn(props)
        await context.request_async(pid, "", timeout=0.01)

    assert 'TimeoutError' in str(excinfo)


@pytest.mark.asyncio
async def test_request_actor_async_should_not_raise_timeout_exception_when_result_is_first():
    props = Props.from_func(hello_function)
    pid = context.spawn(props)
    reply = await context.request_async(pid, "hello", timeout=0.01)

    assert "hey" == reply