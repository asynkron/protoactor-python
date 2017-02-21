#!/usr/bin/env python
# -*- coding: utf-8 -*-


class PID(object):

    def __init__(self, address, id, aref=None):
        self.address = address
        self.id = id
        self.aref = aref

    def __str__(self):
        """Generate a human readable string with the address and ID of
        the PID."""

        return "%(address)s/%(id)s" % {
            "address": self._address,
            "id": self._id
        }
