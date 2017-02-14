#!/usr/bin/env python
# -*- coding: utf-8 -*-


def test_circular_dependencies():
    """Verify that there are no circular dependencies"""
    from protoactor.utils import *
    from protoactor.messages import *
    from protoactor.mailbox import *
    from protoactor.pid import *
    from protoactor.process import *
    from protoactor.processregistry import *
    from protoactor.props import *
