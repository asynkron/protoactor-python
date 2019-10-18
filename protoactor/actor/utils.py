#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from asyncio import Future
from multiprocessing import RLock
from typing import Callable


class Singleton(type):
    _instances = {}
    _singleton_lock = RLock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._singleton_lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def clear(cls):
        try:
            del Singleton._instances[cls]
        except KeyError:
            pass


def python_version():
    """Get the version of python."""

    return sys.version_info[0]


class Stack:
    def __init__(self) -> None:
        self.stack = list()

    def push(self, data: object) -> None:
        self.stack.append(data)

    def pop(self) -> object:
        if self.is_empty():
            raise Exception("nothing to pop")
        return self.stack.pop(len(self.stack) - 1)

    def peek(self) -> Callable[[object], Future]:
        if self.is_empty():
            raise Exception("Nothing to peek")
        return self.stack[len(self.stack) - 1]

    def clear(self) -> None:
        self.stack.clear()

    def is_empty(self) -> bool:
        return len(self.stack) == 0

    def __len__(self) -> int:
        return len(self.stack)