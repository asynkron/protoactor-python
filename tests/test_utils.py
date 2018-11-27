#!/usr/bin/env python
# -*- coding: utf-8 -*-
from protoactor.utils import singleton


def test_singleton():
    class TestSingleton(object, metaclass=singleton):
        def __init__(self):
            self.test = ""

    s1 = TestSingleton()
    s2 = TestSingleton()

    assert s1 is s2


def test_singleton_for_different_classes():
    class A(object, metaclass=singleton):
        def __init__(self):
            self.a = ""

    class B(object, metaclass=singleton):
        def __init__(self):
            self.b = ""

    a = A()
    a1 = A()
    b = B()
    b1 = B()

    assert a is a1
    assert b is b1
    assert not (a is b1)
