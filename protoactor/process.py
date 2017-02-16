#!/usr/bin/env python
# -*- coding: utf-8 -*-
from uuid import uuid4
from messages import MessageSender, Stop


class Process(object):
    """Base class representing a process."""

    def send_user_message(self, pid, message, sender=None):
        raise NotImplementedError("You need to implement this")

    def stop (self, pid):
        self.send_system_message(pid, Stop())

    def send_system_message(self, pid, message):
        raise NotImplementedError("You need to implement this")


class LocalProcess(Process):
    def __init__(self, mailbox):
        self.__mailbox = mailbox

    @property
    def mailbox(self):
        return self.__mailbox

    def send_user_message(self, pid, message, sender=None):
        if sender is not None:
            self.__mailbox.post_user_message(MessageSender(message, sender))
            return

        self.__mailbox.post_user_message(message)

    def send_system_message(self, pid, message):
        self.__mailbox.post_system_message(message)


class DeadLetterEvent(object):

    def __init__(self, pid, message, sender):
        self.__pid = pid
        self.__message = message
        self.__sender = sender

    @property
    def pid(self):
        """Get the PID"""
        return self.__pid

    @property
    def message(self):
        """Get the message"""
        return self.__message

    @property
    def sender(self):
        """Get the sender"""
        return self.__sender


class DeadLettersProcess(Process):

    def send_user_message(self, pid, message, sender=None):
        """Send a user message using the event stream."""
        EventStream().publish(DeadLetterEvent(pid, message, sender))

    def send_system_message(self, pid, message):
        """Send a sytem message using the event stream."""
        EventStream().publish(DeadLetterEvent(pid, message, None))


class EventStream(object):

    def __init__(self):
        self._subscriptions = {}
        self.subscribe(_report_deadletters)

    def subscribe(self, fun):
        """Subscribe to an event stream"""
        uniq_id = uuid4()
        self._subscriptions[uniq_id] = fun

    def publish(self, message):
        """Publish a message to all subscribers"""
        for sub in self._subscriptions.values():
            sub(message)


def _report_deadletters(msg):
    """Print a message for deadletters"""
    if isinstance(msg, DeadLetterEvent):
        msg = """[DeadLetterEvent] %(pid)s got %(message_type)s:%(message)s from
        %(sender)s""" % { "pid": msg.pid,
                         "message_type": type(msg.message),
                         "message": msg.message,
                         "sender": msg.sender
                         }
        print(msg)
