import asyncio

from protoactor import PID, ProcessRegistry
from protoactor.cancel_token import CancelToken
from protoactor.message_envelope import MessageEnvelope
from protoactor.messages import Stop
from protoactor.process import AbstractProcess


class FutureProcess(AbstractProcess):
    def __init__(self, cancellation_token: CancelToken = None) -> None:
        name = ProcessRegistry().next_id()

        self.__pid = ProcessRegistry().add(name, self)
        self.__loop = asyncio.get_event_loop()
        self.__future = self.__loop.create_future()
        self.__cancellation_token = cancellation_token

    @property
    def pid(self) -> PID:
        return self.__pid

    @property
    def task(self) -> asyncio.Future:
        return self.__future

    def send_user_message(self, pid: 'PID', message: object, sender: 'PID' = None) -> None:
        msg = MessageEnvelope.unwrap_message(message)
        if self.__cancellation_token is not None and self.__cancellation_token.triggered:
            self.stop(self.pid)
        else:
            self.__loop.call_soon_threadsafe(self.__future.set_result, msg)
            self.stop(self.pid)

    def send_system_message(self, pid: 'PID', message: object) -> None:
        if isinstance(message, Stop):
            ProcessRegistry().remove(pid)
        else:
            if self.__cancellation_token is None or not self.__cancellation_token.triggered:
                self.__future.set_result(None)
            self.stop(pid)

    async def cancellable_wait(self, timeout: float = None) -> None:
        done, pending = await asyncio.wait({self.__future}, timeout=timeout)

        if not done:
            self.__future.cancel()
            self.stop(self.pid)
            raise TimeoutError()