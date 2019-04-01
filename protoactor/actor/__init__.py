from protoactor.actor.process import ProcessRegistry
from .protos_pb2 import PID


def __tell(self, message):
    ProcessRegistry().get(self).send_user_message(self, message)


def __send_user_message(self, message):
    ProcessRegistry().get(self).send_user_message(self, message)


def __send_system_message(self, message):
    ProcessRegistry().get(self).send_system_message(self, message)


def __stop(self):
    ProcessRegistry().get(self).stop(self)


PID.tell = __tell
PID.send_user_message = __send_user_message
PID.send_system_message = __send_system_message
PID.stop = __stop