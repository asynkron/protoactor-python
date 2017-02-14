#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from protoactor.utils import python_version

if python_version() == 2:
    from Queue import Queue
else:  # Python 3
    from queue import Queue  # pylint:disable=E0401


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
