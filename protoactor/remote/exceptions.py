from protoactor.remote.response import ResponseStatusCode


class ActivatorException(Exception):
    def __init__(self, code: int, do_not_throw: bool = False):
        self.code = code
        self.do_not_throw = do_not_throw


class ActivatorUnavailableException(ActivatorException):
    def __init__(self):
        super().__init__(int(ResponseStatusCode.Unavailable), True)