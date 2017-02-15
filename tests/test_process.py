#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from mock import Mock
from protoactor.process import LocalProcess
from protoactor.mailbox import MailBox
from protoactor.messages import MessageSender


def test_get_mailbox_property():
    mailbox = MailBox()
    lp = LocalProcess(mailbox)

    assert lp.mailbox == mailbox

def test_send_user_message():
    mailbox = MailBox()
    mailbox.post_user_message = Mock()

    lp = LocalProcess(mailbox)
    lp.send_user_message(1, "message")
    mess = mailbox.post_user_message.call_args[0][0]

    assert mess == "message"

def test_send_user_message():
    mailbox = MailBox()
    mailbox.post_system_message = Mock()

    lp = LocalProcess(mailbox)
    lp.send_system_message(1, "message")
    mess = mailbox.post_system_message.call_args[0][0]

    assert mess == "message"

def test_send_user_message_with_sender():
    mailbox = MailBox()
    mailbox.post_user_message = Mock()

    lp = LocalProcess(mailbox)
    lp.send_user_message(1, "message", "sender")
    mess = mailbox.post_user_message.call_args[0][0]

    assert (type(mess) is MessageSender) == True
    assert mess.message == "message"
    assert mess.sender == "sender"

