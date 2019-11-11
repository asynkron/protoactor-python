import threading

is_import = False
if is_import:
    from protoactor.сluster.member_strategy import AbstractMemberStrategy


class RoundRobin:
    def __init__(self, member_strategy: 'AbstractMemberStrategy'):
        self._val = 0
        self._lock = threading.RLock()
        self._member_strategy = member_strategy

    def get_node(self) -> str:
        members = self._member_strategy.get_all_members()
        count = len(members)

        if count == 0:
            return ''
        if count == 1:
            return members[0].address
        with self._lock:
            self._val += 1

        return members[self._val % count].address
