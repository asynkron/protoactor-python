import decimal

from protoactor.actor import PID


class AccountCredited:
    pass


class AccountDebited:
    pass


class ChangeBalance:
    def __init__(self, amount: decimal, reply_to: PID):
        self.amount = amount
        self.reply_to = reply_to


class Credit(ChangeBalance):
    def __init__(self, amount: decimal, reply_to: PID):
        super().__init__(amount, reply_to)


class CreditRefused:
    pass


class Debit(ChangeBalance):
    def __init__(self, amount: decimal, reply_to: PID):
        super().__init__(amount, reply_to)


class DebitRolledBack:
    pass


class EscalateTransfer:
    def __init__(self, message: str):
        self._message = message

    @property
    def message(self):
        return self._message

    def __str__(self):
        return f'{self.__class__.__module__}.{self.__class__.__name__}: {self._message}'


class Result():
    def __init__(self, pid: PID):
        self.pid = pid


class FailedAndInconsistent(Result):
    def __init__(self, pid: PID):
        super().__init__(pid)


class FailedButConsistentResult(Result):
    def __init__(self, pid: PID):
        super().__init__(pid)


class GetBalance:
    pass


class InsufficientFunds:
    pass


class InternalServerError:
    pass


class OK:
    pass


class Refused:
    pass


class ServiceUnavailable:
    pass


class StatusUnknown:
    pass


class SuccessResult(Result):
    def __init__(self, pid: PID):
        super().__init__(pid)


class TransferCompleted:
    def __init__(self, from_id: PID, from_balance: decimal, to: PID, to_balance: decimal):
        self.from_id = from_id
        self.from_balance = from_balance
        self.to = to
        self.to_balance = to_balance

    def __str__(self):
        return f'{self.__class__.__module__}.{self.__class__.__name__}: {self.from_id.id} balance is ' \
               f'{self.from_balance}, {self.to.id} balance is {self.to_balance}'


class TransferFailed():
    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self):
        return f'{self.__class__.__module__}.{self.__class__.__name__}: {self.reason}'


class TransferStarted:
    pass


class UnknownResult(Result):
    def __init__(self, pid: PID):
        super().__init__(pid)
