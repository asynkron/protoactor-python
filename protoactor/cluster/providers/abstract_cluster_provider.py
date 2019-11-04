from abc import ABCMeta, abstractmethod
from typing import List

from protoactor.cluster.member_status import AbstractMemberStatusValue, AbstractMemberStatusValueSerializer


class AbstractClusterProvider(metaclass=ABCMeta):
    @abstractmethod
    async def register_member_async(self, cluster_name: str, host: str, port: int, kinds: List[str],
                                    status_value: AbstractMemberStatusValue,
                                    serializer: AbstractMemberStatusValueSerializer) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def monitor_member_status_changes(self) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def update_member_status_value_async(self, status_value: AbstractMemberStatusValue) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def deregister_member_async(self) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    async def shutdown(self) -> None:
        raise NotImplementedError("Should Implement this method")
