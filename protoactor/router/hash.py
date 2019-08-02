import hashlib
import struct
from typing import List, Callable


class MD5Hasher:
    @staticmethod
    def hash(hash_key: str) -> int:
        digest = hashlib.md5(hash_key.encode()).digest()
        hash_value = struct.unpack('i', digest[:4])[0]
        return hash_value


class HashRing:
    def __init__(self, nodes: List[str], hash_func: Callable[[str], int], replica_count: int) -> None:
        self._ring = []
        self._hash_func = hash_func

        for node in nodes:
            for count in range(replica_count):
                hash_key = str(count) + node
                self._ring.append((self._hash_func(hash_key), node))

        self._ring.sort(key=lambda tup: tup[0])

    def get_node(self, key: str) -> str:
        node = next((t for t in self._ring if t[0] > self._hash_func(key)), None)
        if node is not None:
            return node[1]
        return self._ring[0][1]
