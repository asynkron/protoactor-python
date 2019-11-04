class FNV1A32():
    def __init__(self):
        self._fnv_prime = 0x01000193
        self._fnv_offset_basis = 0x811C9DC5
        self._hash = self._fnv_offset_basis
        self._uint32_max = 0x100000000

    def compute_hash(self, buffer: bytes) -> int:
        self._hash = self._fnv_offset_basis

        if buffer is None:
            raise ValueError('buffer is empty')

        for b in buffer:
            self._hash = self._hash ^ b
            self._hash = (self._hash * self._fnv_prime) % self._uint32_max

        return self._hash
