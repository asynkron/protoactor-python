#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from unittest.mock import Mock
from protoactor.process import LocalProcess, EventStream, DeadLetterEvent
from protoactor.mailbox.mailbox import Mailbox
from protoactor.message_sender import MessageSender


@pytest.fixture(scope='module', )
def process_data():
    mailbox = Mailbox(None, None, None, None)
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


def test_event_stream_publish_subscribe(capsys):
    es = EventStream()

    def fun(x):
        print("fun with %(val)s" % {'val': x})

    es.subscribe(fun)
    es.publish("message")
    out, err = capsys.readouterr()
    assert "fun with" in out


@pytest.mark.skip(reason="not check with capsys.readouterr()")
def test_EventStream_default_subscription_is_called(capsys):
    """Verify that when a DeadLetterEvent is published then
    the default printer is triggered"""
    es = EventStream()
    dlp = DeadLetterEvent(1, 2, 3)
    es.publish(dlp)

    out, err = capsys.readouterr()
    assert "[DeadLetterEvent]" in out
