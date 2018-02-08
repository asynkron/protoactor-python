from abc import abstractmethod, ABCMeta
from protoactor.protos_pb2 import DESCRIPTOR as protos_descriptor
from protoactor.protos_remote_pb2 import DESCRIPTOR as protos_remote_descriptor


class AbstractSerializer(metaclass=ABCMeta):
    @abstractmethod
    def serialize(self, obj):
        raise NotImplementedError('Should implement this method')

    @abstractmethod
    def deserialize(self, bytes_str, type_name):
        raise NotImplementedError('Should implement this method')


class ProtobufSerializer(AbstractSerializer):
    def serialize(self, obj):
        raise NotImplementedError('Should implement this method')

    def deserialize(self, bytes_str, type_name):
        raise NotImplementedError('Should implement this method')


class JsonSerializer(AbstractSerializer):
    def serialize(self, obj):
        raise NotImplementedError('Should implement this method')

    def deserialize(self, bytes_str, type_name):
        raise NotImplementedError('Should implement this method')


__type_lookup = {}
__serializers = []
__protobuf_serializer = ProtobufSerializer()
__default_serializer_id = None


def register_file_descriptor(descriptor):
    for message_name, message_type in descriptor.message_types_by_name.items():
        name = descriptor.package + '.' + message_name
        __type_lookup[name] = message_type.ParseFromString


def register_serializer(serializer, make_default=None):
    __serializers.append(serializer)
    if make_default is None:
        global __default_serializer_id
        __default_serializer_id = len(__serializers) - 1


register_file_descriptor(protos_descriptor)
register_file_descriptor(protos_remote_descriptor)
register_serializer(ProtobufSerializer, True)
register_serializer(JsonSerializer)
