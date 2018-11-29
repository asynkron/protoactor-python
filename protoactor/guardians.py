from protoactor import PID
from protoactor.supervision import AbstractSupervisor


class Guardians:

    @staticmethod
    def get_guardian_pid(strategy: AbstractSupervisor) -> 'PID':
        pass