from protoactor.messages import SystemMessage
from protoactor.utils import singleton


class SuspendMailbox(SystemMessage):
    pass


class ResumeMailbox(SystemMessage):
    pass
