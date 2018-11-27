#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from multiprocessing import RLock


class singleton(type):
    _instances = {}
    _singleton_lock = RLock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._singleton_lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def clear(cls):
        try:
            del singleton._instances[cls]
        except KeyError:
            pass



def python_version():
    """Get the version of python."""

    return sys.version_info[0]
