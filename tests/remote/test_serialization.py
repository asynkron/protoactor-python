# import pytest
#
# from protoactor.actor import PID
# from protoactor.remote.messages import JsonMessage
# from protoactor.remote.serialization import Serialization
#
# from tests.remote.messages.protos_pb2 import DESCRIPTOR


# @pytest.fixture(scope="session", autouse=True)
# def register_file_descriptor():
#     Serialization().register_file_descriptor(DESCRIPTOR)
#
#
# def test_can_serialize_and_deserialize_json_pid():
#     type_name = "actor.PID"
#     json = JsonMessage(type_name, "{ \"address\":\"123\", \"id\":\"456\"}")
#     data = Serialization().serialize(json, 1)
#     deserialized = Serialization().deserialize(type_name, data, 1)
#     assert deserialized.address == "123"
#     assert deserialized.id == "456"
#
#
# def test_can_serialize_and_deserialize_json():
#     type_name = "remote_test_messages.Ping"
#     json = JsonMessage(type_name, "{ \"message\":\"Hello\"}")
#     data = Serialization().serialize(json, 1)
#     deserialized = Serialization().deserialize(type_name, data, 1)
#     assert deserialized.message == "Hello"
#
#
# def test_can_serialize_and_deserialize_protobuf():
#     type_name = "actor.PID"
#     pid = PID(address='123', id='456')
#     data = Serialization().serialize(pid, 0)
#     deserialized = Serialization().deserialize(type_name, data, 0)
#     assert deserialized.address == "123"
#     assert deserialized.id == "456"
