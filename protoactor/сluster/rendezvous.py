from protoactor.сluster.hash_algorithms.fnv1a32 import FNV1A32

is_import = False
if is_import:
    from protoactor.сluster.member_strategy import AbstractMemberStrategy


class Rendezvous:
    def __init__(self, member_strategy: 'AbstractMemberStrategy'):
        self._member_strategy = member_strategy
        self._hash_algorithm = FNV1A32()
        self._member_hashes = None
        self.update_rdv()

    def get_node(self, key: str):
        members = self._member_strategy.get_all_members()
        if members is None or len(members) == 0:
            return ''

        if len(members) == 1:
            return members[0].address

        key_bytes = key.encode()
        max_score = 0
        max_node = None

        for i in range(len(members)):
            member = members[i]
            if member.alive:
                hash_bytes = self._member_hashes[i]
                score = self._rdv_hash(hash_bytes, key_bytes)
                if score > max_score:
                    max_score = score
                    max_node = member

        if max_node is None:
            return ''
        else:
            return max_node.address

    def update_rdv(self):
        self._member_hashes = [member.address.encode() for member in self._member_strategy.get_all_members()]

    def _rdv_hash(self, node: bytes, key: bytes) -> int:
        hash_bytes = key + node
        return self._hash_algorithm.compute_hash(hash_bytes)
