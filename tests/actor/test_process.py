#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from unittest.mock import Mock
from protoactor.actor.process import ActorProcess
from protoactor.mailbox.mailbox import DefaultMailbox


@pytest.fixture(scope='module', )
def process_data():
    mailbox = DefaultMailbox(None, None, None)
    local_process = ActorProcess(mailbox)

    return {
        'mailbox': mailbox,
        'local_process': local_process,
    }


def test_get_mailbox_property(process_data):
    mailbox = process_data['mailbox']
    lp = process_data['local_process']

    assert lp.mailbox == mailbox

@pytest.mark.asyncio
async def test_send_user_message(process_data):
    mailbox = process_data['mailbox']
    lp = process_data['local_process']

    mailbox.post_user_message = Mock()
    await lp.send_user_message(1, "message")
    mess = mailbox.post_user_message.call_args[0][0]

    assert mess == "message"