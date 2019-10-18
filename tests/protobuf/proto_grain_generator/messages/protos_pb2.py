# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: tests/protobuf/proto_grain_generator/messages/protos.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='tests/protobuf/proto_grain_generator/messages/protos.proto',
  package='messages',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n:tests/protobuf/proto_grain_generator/messages/protos.proto\x12\x08messages\"\x0e\n\x0cHelloRequest\" \n\rHelloResponse\x12\x0f\n\x07Message\x18\x01 \x01(\t2K\n\nHelloGrain\x12=\n\x08SayHello\x12\x16.messages.HelloRequest\x1a\x17.messages.HelloResponse\"\x00\x62\x06proto3')
)




_HELLOREQUEST = _descriptor.Descriptor(
  name='HelloRequest',
  full_name='messages.HelloRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=72,
  serialized_end=86,
)


_HELLORESPONSE = _descriptor.Descriptor(
  name='HelloResponse',
  full_name='messages.HelloResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='Message', full_name='messages.HelloResponse.Message', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=88,
  serialized_end=120,
)

DESCRIPTOR.message_types_by_name['HelloRequest'] = _HELLOREQUEST
DESCRIPTOR.message_types_by_name['HelloResponse'] = _HELLORESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

HelloRequest = _reflection.GeneratedProtocolMessageType('HelloRequest', (_message.Message,), {
  'DESCRIPTOR' : _HELLOREQUEST,
  '__module__' : 'tests.protobuf.proto_grain_generator.messages.protos_pb2'
  # @@protoc_insertion_point(class_scope:messages.HelloRequest)
  })
_sym_db.RegisterMessage(HelloRequest)

HelloResponse = _reflection.GeneratedProtocolMessageType('HelloResponse', (_message.Message,), {
  'DESCRIPTOR' : _HELLORESPONSE,
  '__module__' : 'tests.protobuf.proto_grain_generator.messages.protos_pb2'
  # @@protoc_insertion_point(class_scope:messages.HelloResponse)
  })
_sym_db.RegisterMessage(HelloResponse)



_HELLOGRAIN = _descriptor.ServiceDescriptor(
  name='HelloGrain',
  full_name='messages.HelloGrain',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=122,
  serialized_end=197,
  methods=[
  _descriptor.MethodDescriptor(
    name='SayHello',
    full_name='messages.HelloGrain.SayHello',
    index=0,
    containing_service=None,
    input_type=_HELLOREQUEST,
    output_type=_HELLORESPONSE,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_HELLOGRAIN)

DESCRIPTOR.services_by_name['HelloGrain'] = _HELLOGRAIN

# @@protoc_insertion_point(module_scope)
