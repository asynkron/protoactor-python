from abc import ABCMeta, abstractmethod


class AbstractInvoker(metaclass=ABCMeta):
    @abstractmethod
    async def invoke_system_message(self, message: object) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def invoke_user_message(self, message: object) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def escalate_failure(self, reason: Exception, message: object) -> None:
        raise NotImplementedError("Should Implement this method")
