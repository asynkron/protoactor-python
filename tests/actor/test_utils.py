#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from protoactor.actor.utils import Singleton, Stack


@pytest.fixture
def stack():
    return Stack()


def test_singleton():
    class TestSingleton(metaclass=Singleton):
        def __init__(self):
            self.test = ""

    s1 = TestSingleton()
    s2 = TestSingleton()

    assert s1 is s2


def test_singleton_for_different_classes():
    class A(metaclass=Singleton):
        def __init__(self):
            self.a = ""

    class B(metaclass=Singleton):
        def __init__(self):
            self.b = ""

    a = A()
    a1 = A()
    b = B()
    b1 = B()

    assert a is a1
    assert b is b1
    assert not a is b1


def test_stack_push_pop(stack):
    stack.push("Test data")
    assert stack.pop() == "Test data"


def test_stack_push_peek_len(stack):
    stack.push("Test data")
    assert stack.peek() == "Test data"
    assert len(stack) == 1


def test_stack_push_is_empty(stack):
    stack.push("Test data")
    assert stack.is_empty() is False