from datetime import datetime, timedelta
from typing import Optional


class RestartStatistics:

    def __init__(self, failure_count: int, last_failure_time: Optional[datetime]) -> None:
        self.__failure_count = failure_count
        self.__last_failure_time = last_failure_time

    @property
    def failure_count(self) -> int:
        return self.__failure_count

    @property
    def last_failure_time(self) -> datetime:
        return self.__last_failure_time

    def fail(self) -> None:
        self.__failure_count += 1

    def reset(self) -> None:
        self.__last_failure_time = 0

    def restart(self) -> None:
        self.__last_failure_time = datetime.now()

    def is_within_duration(self, within: timedelta) -> bool:
        return (datetime.now() - self.last_failure_time) < within
