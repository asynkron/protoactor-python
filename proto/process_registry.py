from multiprocessing import Lock

from .process import AbstractProcess

class ProcessRegistry:

    __id = 0

    @classmethod
    def get(cls, pid) -> AbstractProcess:
        pass

    @classmethod
    def next_id(cls) -> str:
        with Lock():
            ProcessRegistry.__id =  ProcessRegistry.__id + 1

        return str(ProcessRegistry.__id)