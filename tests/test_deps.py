#!/usr/bin/env python
# -*- coding: utf-8 -*-


def test_circular_dependencies():
    """Verify that there are no circular dependencies"""
    from protoactor.utils import singleton, python_version
    from protoactor.messages import AutoReceiveMessage
    from protoactor.mailbox import MailBox
    from protoactor.pid import PID
    from protoactor.process import DeadLetterEvent
    from protoactor.process_registry import ProcessRegistry
    from protoactor.props import Props
