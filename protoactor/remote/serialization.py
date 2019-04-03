from abc import abstractmethod, ABCMeta

from google.protobuf import json_format
from google.protobuf.message import Message

from protoactor.actor.protos_pb2 import DESCRIPTOR as protos_descriptor
from protoactor.actor.utils import singleton
from protoactor.remote.messages import JsonMessage
from protoactor.remote.protos_remote_pb2 import DESCRIPTOR as protos_remote_descriptor


class AbstractSerializer(metaclass=ABCMeta):
    @abstractmethod
    def serialize(self, obj):
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def deserialize(self, bytes_str, type_name):
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def get_type_name(self, message):
        raise NotImplementedError('Should implement this method')


class ProtobufSerializer(AbstractSerializer):
    def serialize(self, obj):
        if not isinstance(obj, Message):
            raise TypeError("obj must be of type Message")
        return obj.SerializeToString()

    def deserialize(self, bytes_str, type_name):
        message_descriptor = Serialization().type_lookup[type_name]
        msg = message_descriptor._concrete_class()
        msg.ParseFromString(bytes_str)
        return msg

    def get_type_name(self, obj):
        if not isinstance(obj, Message):
            raise TypeError("obj must be of type Message")
        return obj.DESCRIPTOR.full_name


class JsonSerializer(AbstractSerializer):
    def serialize(self, obj):
        if isinstance(obj, JsonMessage):
            return str.encode(obj.json)
        return json_format.MessageToJson(obj)

    def deserialize(self, bytes_str, type_name):
        message_descriptor = Serialization().type_lookup[type_name]
        msg = message_descriptor._concrete_class()
        json_format.Parse(bytes_str, msg)
        return msg

    def get_type_name(self, obj):
        if isinstance(obj, JsonMessage):
            return obj.type_name
        if not isinstance(obj, Message):
            raise TypeError("obj must be of type Message")
        return obj.DESCRIPTOR.full_name


class Serialization(metaclass=singleton):
    def __init__(self):
        self.type_lookup = {}
        self.__serializers = []
        self.__protobuf_serializer = ProtobufSerializer()
        self.__default_serializer_id = None

        self.register_file_descriptor(protos_descriptor)
        self.register_file_descriptor(protos_remote_descriptor)
        self.register_serializer(ProtobufSerializer(), True)
        self.register_serializer(JsonSerializer())

    @property
    def default_serializer_id(self):
        return self.__default_serializer_id

    @default_serializer_id.setter
    def default_serializer_id(self, value):
        self.__default_serializer_id = value

    def register_serializer(self, serializer, make_default=False):
        self.__serializers.append(serializer)
        if make_default:
            self.__default_serializer_id = len(self.__serializers) - 1

    def register_file_descriptor(self, descriptor):
        for message_name, message_type in descriptor.message_types_by_name.items():
            name = descriptor.package + '.' + message_name
            self.type_lookup[name] = message_type

    def serialize(self, message, serializer_id):
        return self.__serializers[serializer_id].serialize(message)

    def get_type_name(self, message, serializer_id):
        return self.__serializers[serializer_id].get_type_name(message)

    def deserialize(self, type_name, data, serializer_id):
        return self.__serializers[serializer_id].deserialize(data, type_name)
