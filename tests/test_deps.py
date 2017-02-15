#!/usr/bin/env python
# -*- coding: utf-8 -*-


def test_circular_dependencies():
    """Verify that there are no circular dependencies"""
    from master_protoactor.utils import *
    from master_protoactor.messages import *
    from master_protoactor.mailbox import *
    from master_protoactor.pid import *
    from master_protoactor.process import *
    from master_protoactor.processregistry import *
    from master_protoactor.props import *
