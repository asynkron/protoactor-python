import asyncio
from datetime import timedelta
from threading import Thread


class AsyncTimer(Thread):
    def __init__(self, interval: timedelta, function, args=None, kwargs=None):
        super().__init__()
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.loop = None
        self._task = None
        self._cancelled = False

    def run(self):
        self.loop = asyncio.new_event_loop()
        loop = self.loop
        asyncio.set_event_loop(loop)
        try:
            self._task = asyncio.ensure_future(self._job())
            loop.run_until_complete(self._task)
        finally:
            loop.close()

    def cancel(self):
        if self.loop is not None:
            self._cancelled = True

    async def _job(self):
        await asyncio.sleep(self.interval.total_seconds())
        if not self._cancelled:
            await self.function(*self.args, **self.kwargs)
