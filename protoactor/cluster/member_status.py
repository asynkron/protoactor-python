from abc import abstractmethod, ABCMeta
from typing import List


class AbstractMemberStatusValue(metaclass=ABCMeta):
    @abstractmethod
    def is_same(self, val: 'AbstractMemberStatusValue') -> bool:
        raise NotImplementedError("Should Implement this method")


class AbstractMemberStatusValueSerializer(metaclass=ABCMeta):
    @abstractmethod
    def to_value_bytes(self, val: AbstractMemberStatusValue) -> bytes:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def from_value_bytes(self, val: bytes) -> AbstractMemberStatusValue:
        raise NotImplementedError("Should Implement this method")


class MemberStatus:
    def __init__(self, member_id: str, host: str, port: int, kinds: List[str], alive: bool,
                 status_value: AbstractMemberStatusValue):
        self._member_id = member_id
        if host is None:
            raise ValueError('host not set')
        self._host = host
        if kinds is None:
            raise ValueError('kinds not set')
        self._kinds = kinds
        self._port = port
        self._alive = alive
        self._status_value = status_value

    @property
    def address(self) -> str:
        return self._host + ':' + str(self._port)

    @property
    def member_id(self) -> str:
        return self._member_id

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def kinds(self) -> List[str]:
        return self._kinds

    @property
    def alive(self) -> bool:
        return self._alive

    @property
    def status_value(self) -> AbstractMemberStatusValue:
        return self._status_value


class NullMemberStatusValueSerializer(AbstractMemberStatusValueSerializer):
    def to_value_bytes(self, val: AbstractMemberStatusValue) -> bytes:
        return None

    def from_value_bytes(self, val: bytes) -> AbstractMemberStatusValue:
        return None