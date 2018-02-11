from protoactor.messages import SystemMessage


class SuspendMailbox(SystemMessage):
    pass


class ResumeMailbox(SystemMessage):
    pass
