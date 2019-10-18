from abc import abstractmethod, ABCMeta
from typing import List

from protoactor.сluster.member_status import MemberStatus
from protoactor.сluster.rendezvous import Rendezvous
from protoactor.сluster.round_robin import RoundRobin


class AbstractMemberStrategy(metaclass=ABCMeta):
    @abstractmethod
    def get_all_members(self) -> List[MemberStatus]:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def add_member(self, member: MemberStatus) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def update_member(self, member: MemberStatus) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def remove_member(self, member: MemberStatus) -> None:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def get_partition(self, key) -> str:
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def get_activator(self) -> str:
        raise NotImplementedError("Should Implement this method")


class SimpleMemberStrategy(AbstractMemberStrategy):
    def __init__(self):
        self._members = []
        self._rdv = Rendezvous(self)
        self._rr = RoundRobin(self)

    def get_all_members(self) -> List[MemberStatus]:
        return self._members

    def add_member(self, member: MemberStatus) -> None:
        self._members.append(member)
        self._rdv.update_rdv()

    def update_member(self, member: MemberStatus) -> None:
        for i in range(len(self._members)):
            if self._members[i].address == member.address:
                self._members[i] = member

    def remove_member(self, member: MemberStatus) -> None:
        for i in range(len(self._members)):
            if self._members[i].address == member.address:
                del self._members[i]
                self._rdv.update_rdv()

    def get_partition(self, key) -> str:
        return self._rdv.get_node(key)

    def get_activator(self) -> str:
        return self._rr.get_node()

