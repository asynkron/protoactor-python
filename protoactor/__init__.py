#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = "0.0.1"

from .protos_pb2 import PID
from process import LocalProcess, DeadLettersProcess
from process_registry import ProcessRegistry

def create_pid(address, id, ref):
    p = PID()
    p.address = address
    p.id = id
    p.process = ref

    return p


def __ref (self):
    if self.process is not None:
        if isinstance(self.process, LocalProcess) and self.process.is_dead:
            self.process = None

        return self.process

    reff = ProcessRegistry().get(self)
    if not(isinstance(reff, DeadLettersProcess)):
        self.process = reff

    return self.process


def __tell(self, message):
    self.ref.send_user_message(this, message)


def __send_system_message(self, message):
    self.ref.send_system_message(self, message)
    

PID.process = None
PID.ref = __ref
PID.tell = __tell
PID.send_system_message = __send_system_message
