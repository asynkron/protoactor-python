#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from queue import Queue


class MailboxType(object):
    mailboxIdle, mailboxBusy = 0, 1


class _MailboxQueue(object):
    """Base class to provide a number of interface functions that a queued
    enabled mailbox exposes"""

    def push(self, message):
        raise NotImplementedError("Implement this on a subclass")

    def pop(self):
        raise NotImplementedError("Implement this on a subclass")

    def has_messages(self):
        raise NotImplementedError("Implement this on a subclass")


class UnboundedMailboxQueue(_MailboxQueue):
    """Implementation of an unbounded mailbox"""

    def __init__(self):
        _MailboxQueue.__init__(self)
        self._queue = Queue()

    def push(self, message):
        self._queue.put(message)

    def pop(self):
        return self._queue.get()

    def has_messages(self):
        return not self._queue.empty()


class MailBox(object):

    def post_user_message(self, msg):
        raise NotImplementedError("Implement this on a subclass")

    def post_system_message(self, msg):
        raise NotImplementedError("Implement this on a subsclass")

    def post_system_message(self, invoker, dispatcher):
        raise NotImplementedError("Implement this on a subclass")

    def start(self):
        raise NotImplementedError("Implement this on a subclass")
