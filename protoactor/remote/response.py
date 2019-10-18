from enum import Enum


class ResponseStatusCode(Enum):
    OK = 0
    Unavailable = 1
    Timeout = 2
    ProcessNameAlreadyExist = 3
    Error = 4