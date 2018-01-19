#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = "0.0.1"

from .protos_pb2 import PID
from .process_registry import ProcessRegistry
# from .process import LocalProcess, DeadLettersProcess


def __tell(self, message):
    ProcessRegistry().get(self).send_user_message(self, message)


def __send_system_message(self, message):
    ProcessRegistry().get(self).send_system_message(self, message)


PID.tell = __tell
PID.send_system_message = __send_system_message
