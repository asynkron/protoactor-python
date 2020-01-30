from typing import Callable


class ForWithProgress:
    def __init__(self, total: int, every_nth: int, run_both_on_every: bool, run_on_start: bool):
        self._total = total
        self._every_nth = every_nth
        self._run_both_on_every = run_both_on_every
        self._run_on_start = run_on_start

    def every_nth(self, every_nth_action: Callable[[int], None], every_action: Callable[[int, bool], None])->None:
        def must_run_nth(current: int) -> bool:
            if current == 0 and self._run_on_start:
                return True
            if current == 0:
                return False
            return current % self._every_nth == 0

        for i in range(self._total+1):
            must = must_run_nth(i)
            if must:
                every_nth_action(i)
            if must and not self._run_both_on_every:
                continue
            every_action(i, must)