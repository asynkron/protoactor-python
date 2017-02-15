from messages import MessageSender, Stop

class Process(object):
    def send_user_message(self, pid, message, sender=None):
        pass

    def stop (self, pid):
        self.send_system_message(pid, Stop())

    def send_system_message(self, pid, message):
        pass


class LocalProcess(Process):
    def __init__(self, mailbox):
        self.__mailbox = mailbox

    @property
    def mailbox(self):
        return self.__mailbox

    def send_user_message(self, pid, message, sender=None):
        if sender is not None:
            self.__mailbox.post_user_message(MessageSender(message, sender))
            return

        self.__mailbox.post_user_message(message)

    def send_system_message(self, pid, message):
        self.__mailbox.post_system_message(message)


class DeadLettersProcess(Process):
    pass
    