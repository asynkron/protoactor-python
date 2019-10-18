from typing import List


class ProtoMessage:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name


class ProtoMethod:
    def __init__(self, index: int, name: str, input_name: str, output_name: str):
        self._index = index
        self._name = name
        self._input_name = input_name
        self._output_name = output_name

    @property
    def index(self) -> int:
        return self._index

    @property
    def name(self) -> str:
        return self._name

    @property
    def input_name(self) -> str:
        return self._input_name

    @property
    def output_name(self) -> str:
        return self._output_name


class ProtoService:
    def __init__(self, name: str, methods: List[str] = None):
        if methods is None:
            methods = []
        self._name = name
        self._methods = methods

    @property
    def name(self) -> str:
        return self._name

    @property
    def methods(self) -> List[ProtoMethod]:
        return self._methods


class ProtoFile:
    def __init__(self, messages=None, services=None):
        if services is None:
            services = []
        if messages is None:
            messages = []
        self._messages = messages
        self._services = services

    @property
    def messages(self) -> List[ProtoMessage]:
        return self._messages

    @property
    def services(self) -> List[ProtoService]:
        return self._services
