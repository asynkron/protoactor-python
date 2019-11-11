from abc import ABCMeta
from typing import List

from protoactor.сluster.member_status import MemberStatus


class ClusterTopologyEvent():
    def __init__(self, statuses: List[MemberStatus]):
        if statuses is None:
            raise ValueError('statuses is empty')
        self._statuses = statuses

    @property
    def statuses(self) -> List[MemberStatus]:
        return self._statuses


class AbstractMemberStatusEvent(metaclass=ABCMeta):
    def __init__(self, host: str, port: int, kinds: List[str]):
        if host is None:
            raise ValueError('host is none')
        self._host = host
        self._port = port

        if kinds is None:
            raise ValueError('kinds is none')
        self._kinds = kinds

    @property
    def address(self) -> str:
        return self._host + ":" + str(self._port)

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def kinds(self) -> List[str]:
        return self._kinds


class MemberJoinedEvent(AbstractMemberStatusEvent):
    def __init__(self, host: str, port: int, kinds: List[str]):
        super().__init__(host, port, kinds)


class MemberRejoinedEvent(AbstractMemberStatusEvent):
    def __init__(self, host: str, port: int, kinds: List[str]):
        super().__init__(host, port, kinds)


class MemberLeftEvent(AbstractMemberStatusEvent):
    def __init__(self, host: str, port: int, kinds: List[str]):
        super().__init__(host, port, kinds)
