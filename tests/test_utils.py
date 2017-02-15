#!/usr/bin/env python
# -*- coding: utf-8 -*-
from master_protoactor.utils import singleton


def test_python_version_does_not_break():

    @singleton
    class TestSingleton(object):
        def __init__(self):
            self.test = ""

    s1 = TestSingleton()
    s2 = TestSingleton()

    assert s1 is s2
