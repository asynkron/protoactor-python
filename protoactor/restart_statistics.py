#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime


class RestartStatistics(object):
    def __init__(self, failure_count, last_failure_time):
        self.__failure_count = failure_count
        self.__last_failure_time = last_failure_time

    def request_restart_permission(self, max_retries_number, within_timedelta=None):
        if max_retries_number == 0:
            return False

        self.__failure_count += 1

        if within_timedelta is None:
            return self.__failure_count <= max_retries_number

        max = datetime.datetime.now() - within_timedelta
        
        if self.__last_failure_time > max:
            return self.__failure_count <= max_retries_number

        self.__failure_count = 0
        return True
