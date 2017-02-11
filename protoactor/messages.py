#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from protoactor.utils import singleton


class SystemMessage(object):
    pass


class AutoReceiveMessage(object):
    pass


class Terminated(SystemMessage):
    pass


@singleton
class SuspendMailbox(SystemMessage):
    pass


@singleton
class ResumeMailbox(SystemMessage):
    pass


class Failure(SystemMessage):

    def __init__(self, who, reason):
        self.who = who
        self.reason = reason

    @property
    def who(self):
        return self.who

    @property
    def reason(self):
        return self.reason


class Watch(SystemMessage):

    def __init__(self, watcher):
        self.watcher = watcher


class Unwatch(SystemMessage):

    def __init__(self, watcher):
        self.watcher = watcher


@singleton
class Restart(SystemMessage):
    pass


@singleton
class Stop(SystemMessage):
    pass


@singleton
class Stopping(AutoReceiveMessage):
    pass


@singleton
class Started(AutoReceiveMessage):
    pass


@singleton
class Stopped(AutoReceiveMessage):
    pass


class MessageSender(object):

    def __init__(self, message, sender):
        self._message = message
        self._sender = sender

    @property
    def message(self):
        """Return the message."""
        return self._message

    @property
    def sender(self):
        """Return the sender PID."""
        return self._sender
