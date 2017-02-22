#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from multiprocessing import RLock


def singleton(cls):
    """Decorator to create singleton classes"""

    instances = {}
    lock = RLock()

    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


def python_version():
    """Get the version of python."""

    return sys.version_info[0]
