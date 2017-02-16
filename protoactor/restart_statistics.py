import datetime
from typing import Optional


class RestartStatistics:
    def __init__(self, failure_count: int, last_failure_time: Optional[datetime.datetime]):
        self.__failure_count = failure_count
        self.__last_failure_time = last_failure_time

    @property
    def failure_count(self) -> int:
        return self.__failure_count

    @property
    def last_failure_time(self) -> datetime.datetime:
        return self.__last_failure_time

    def request_restart_permission(self, max_retries_number: int, within_timedelta: datetime.timedelta = None):
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
