#!/usr/bin/env python
# -*- coding: utf-8 -*-
from protoactor import protos_pb2
from protoactor.process_registry import ProcessRegistry
__version__ = "0.0.1"


def __get_process(self):
    pr = ProcessRegistry()
    reff = pr.get(self)
    return reff


def tell(self, message):
    self.process.send_user_message(self, message)


def send_system_message(self, message):
    self.process.send_system_message(self, message)


def stop(self):
    self.process.stop()


protos_pb2.PID.process = property(__get_process)
protos_pb2.PID.tell = tell
protos_pb2.PID.send_system_message = send_system_message
protos_pb2.PID.stop = stop
