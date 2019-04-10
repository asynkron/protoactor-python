#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from protoactor.mailbox import queue


@pytest.fixture
def unbounded_queue():
    return queue.UnboundedMailboxQueue()


def test_unbounded_mailbox_queue_push_pop(unbounded_queue):
    unbounded_queue.push("1")
    assert unbounded_queue.pop() == "1"


def test_unbounded_mailbox_queue_pop_empty(unbounded_queue):
    assert unbounded_queue.pop() is None


def test_unbounded_mailbox_queue_has_message(unbounded_queue):
    unbounded_queue.push("1")
    assert unbounded_queue.has_messages() is True


def test_unbounded_mailbox_queue_has_message_empty(unbounded_queue):
    assert unbounded_queue.has_messages() is False


def test_create_abstract_queue():
    with pytest.raises(TypeError):
        _queue = queue.AbstractQueue()
