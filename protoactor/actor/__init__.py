from protoactor.actor.protos_pb2 import PID
from protoactor.actor.process import ProcessRegistry


async def __tell(self, message):
    await ProcessRegistry().get(self).send_user_message(self, message)


async def __send_user_message(self, message):
    await ProcessRegistry().get(self).send_user_message(self, message)


async def __send_system_message(self, message):
    await ProcessRegistry().get(self).send_system_message(self, message)


async def __stop(self):
    await ProcessRegistry().get(self).stop(self)


def __to_short_string(self):
    return self.address + '/' + self.id


PID.tell = __tell
PID.send_user_message = __send_user_message
PID.send_system_message = __send_system_message
PID.stop = __stop
PID.to_short_string = __to_short_string
