from datetime import datetime, timedelta
from typing import Optional


class RestartStatistics:

    def __init__(self, failure_count: int, last_failure_time: Optional[datetime]) -> None:
        self.__failures_items = []
        for i in range(0, failure_count):
            self.__failures_items.append(last_failure_time or datetime.now())

    @property
    def failure_count(self) -> int:
        return len(self.__failures_items)

    def fail(self) -> None:
        self.__failures_items.append(datetime.now())

    def reset(self) -> None:
        self.__failures_items.clear()

    def number_of_failures(self, within: timedelta) -> int:
        res = 0

        if within is not None:
            for failure_item in self.__failures_items:
                if datetime.now() - failure_item < within:
                    res += 1
        else:
            res = len(self.__failures_items)

        return res
