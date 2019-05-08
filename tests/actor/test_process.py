#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from unittest.mock import Mock
from protoactor.actor.process import LocalProcess
from protoactor.mailbox.mailbox import DefaultMailbox
from protoactor.actor.message_sender import MessageSender


@pytest.fixture(scope='module', )
def process_data():
    mailbox = DefaultMailbox(None, None, None)
    local_process = LocalProcess(mailbox)

    return {
        'mailbox': mailbox,
        'local_process': local_process,
    }


def test_get_mailbox_property(process_data):
    mailbox = process_data['mailbox']
    lp = process_data['local_process']

    assert lp.mailbox == mailbox


def test_send_user_message(process_data):
    mailbox = process_data['mailbox']
    lp = process_data['local_process']

    mailbox.post_user_message = Mock()
    lp.send_user_message(1, "message")
    mess = mailbox.post_user_message.call_args[0][0]

    assert mess == "message"


def test_send_user_message_with_sender(process_data):
    mailbox = process_data['mailbox']
    lp = process_data['local_process']

    mailbox.post_user_message = Mock()
    lp.send_user_message(1, "message", "sender")
    mess = mailbox.post_user_message.call_args[0][0]

    assert isinstance(mess, MessageSender) is True
    assert mess.message == "message"
    assert mess.sender == "sender"