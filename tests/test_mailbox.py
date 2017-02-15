#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from master_protoactor.mailbox import UnboundedMailboxQueue, _MailboxQueue


def test_mailbox_adds():
    mailbox = UnboundedMailboxQueue()
    mailbox.push("1")


def test_mailbox_has_messages_returns_false_when_empty():
    mailbox = UnboundedMailboxQueue()
    assert mailbox.has_messages() == False


def test_mailbox_adds_successfully():
    mailbox = UnboundedMailboxQueue()
    mailbox.push("1")
    assert mailbox.has_messages() == True


def test_mailbox_removes_successfully():
    mailbox = UnboundedMailboxQueue()
    mailbox.push("1")
    msg = mailbox.pop()
    assert msg == "1"


def test_mailbox_queue_throws_not_implemented():
    mailbox = _MailboxQueue()
    with pytest.raises(NotImplementedError):
        mailbox.push("1")


def test_mailbox_queue_removes_throws_not_implemented():
    mailbox = _MailboxQueue()
    with pytest.raises(NotImplementedError):
        mailbox.pop()
