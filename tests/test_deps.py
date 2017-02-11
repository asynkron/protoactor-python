#!/usr/bin/env python
# -*- coding: utf-8 -*-


def test_circular_dependencies():
    """Verify that there are no circular dependencies"""
    from protoactor.utils import *
    from protoactor.messages import *
