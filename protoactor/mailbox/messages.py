from protoactor.actor.messages import SystemMessage


class SuspendMailbox(SystemMessage):
    pass


class ResumeMailbox(SystemMessage):
    pass
