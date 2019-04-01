from abc import ABCMeta, abstractmethod


class AbstractMailBoxStatistics(metaclass=ABCMeta):
    @abstractmethod
    def mailbox_stated(self):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def message_posted(self, message):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def message_received(self, message):
        raise NotImplementedError("Should Implement this method")

    @abstractmethod
    def mailbox_empty(self):
        raise NotImplementedError("Should Implement this method")


class MailBoxStatistics(AbstractMailBoxStatistics):
    def mailbox_stated(self):
        raise NotImplementedError("Should Implement this method")

    def message_posted(self, message):
        raise NotImplementedError("Should Implement this method")

    def message_received(self, message):
        raise NotImplementedError("Should Implement this method")

    def mailbox_empty(self):
        raise NotImplementedError("Should Implement this method")