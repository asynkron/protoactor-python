from protoactor.mailbox.mailbox import DefaultMailbox
from protoactor.mailbox.queue import UnboundedMailboxQueue


class MockMailbox(DefaultMailbox):
    def __init__(self):
        super().__init__(UnboundedMailboxQueue(), UnboundedMailboxQueue(), [])
        self.user_messages = []
        self.system_messages = []

    def post_user_message(self, msg):
        self.user_messages.append(msg)
        super().post_user_message(msg)

    def post_system_message(self, msg):
        self.system_messages.append(msg)
        super().post_system_message(msg)