class Snapshot:
    def __init__(self, state: any, index: int):
        self.state = state
        self.index = index


class RecoverSnapshot(Snapshot):
    def __init__(self, data: any, index: int):
        super().__init__(data, index)


class PersistedSnapshot(Snapshot):
    def __init__(self, data: any, index: int):
        super().__init__(data, index)


class Event:
    def __init__(self, data: any, index: int):
        self.data = data
        self.index = index


class RecoverEvent(Event):
    def __init__(self, data: any, index: int):
        super().__init__(data, index)


class ReplayEvent(Event):
    def __init__(self, data: any, index: int):
        super().__init__(data, index)


class PersistedEvent(Event):
    def __init__(self, data: any, index: int):
        super().__init__(data, index)