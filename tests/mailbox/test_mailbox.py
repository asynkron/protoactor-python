#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from protoactor.mailbox import mailbox


def test_create_abstract_mailbox():
    with pytest.raises(TypeError):
        _mailbox = mailbox.AbstractMailbox()
