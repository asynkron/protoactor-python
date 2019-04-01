from enum import IntEnum


class ResponseStatusCode(IntEnum):
    OK = 1
    Unavailable = 2
    Timeout = 3
    ProcessNameAlreadyExist = 4
    Error = 5