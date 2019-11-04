import traceback

import pytest

@pytest.mark.asyncio
async def test_send_message_through_root_context_decorator():
    try:
        raise OSError('aaa')
    except Exception as ex:
        q = type(ex).__name__
        q1 = traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)
        q1 = traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)