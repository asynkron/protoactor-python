from protoactor.cluster.hash_algorithms.fnv1a32 import FNV1A32


def test_hash_function():
    hash_algorithm = FNV1A32()
    assert hash_algorithm.compute_hash('Test'.encode()) == 805092869
    assert hash_algorithm.compute_hash('Test 2'.encode()) == 3918614647