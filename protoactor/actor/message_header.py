import collections


class MessageHeader(collections.Mapping):

    def __init__(self, data=None):
        if data is None:
            data = {}
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def extend(self, key=None, value=None, items=None):
        if key is not None and value is not None:
            self._data[key] = value
        elif items is not None:
            self._data.update(items)
        return MessageHeader(self._data)

    @staticmethod
    def empty():
        return MessageHeader()