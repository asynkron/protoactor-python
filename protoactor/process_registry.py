#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from pid import PID
from process import DeadLettersProcess

non_host = "nonhost"


class ProcessRegistry(object):

    def __init__(self, resolver):
        self._hostResolvers = [resolver]
        # python dict structure is atomic for primitive actions. Need to be checked
        self.__local_actor_refs = {}
        self.__sequence_id = 0
        self.address = non_host
        self._lock = threading.Lock()

    def get(self, pid):
        """Get the process ID from the process registry."""

        if pid.address not in [non_host, self.address]:
            for resolver in self._hostResolvers:
                reff = resolver(pid)
                if reff is None:
                    continue
               		
                pid.aref = reff
                return reff
	
        aref = self.__local_actor_refs.get(pid.id, None)
        if aref is not None:
            return aref
	
        return DeadLettersProcess()

    def add(self, id, aref):
        pid = PID(id=id, aref=aref, address=self.address)
        self.__local_actor_refs[id] = aref
        return pid

    def remove(self, pid):
        self.__local_actor_refs.pop(pid.id)

    def next_id(self):
        with self._lock:
            self.__sequence_id += 1
        return self.__sequence_id
