import pytest

from protoactor.actor import PID
from protoactor.actor.message_envelope import MessageEnvelope
from protoactor.actor.message_header import MessageHeader


@pytest.fixture()
def message_envelope():
    message = "test"
    sender = PID()
    sender.address = "test"
    sender.id = "test"
    header = MessageHeader()
    return MessageEnvelope(message, sender, header)


def test_wrap(message_envelope):
    envelope = MessageEnvelope.wrap(message_envelope.message)
    assert message_envelope.message == envelope.message


def test_create_new_message_envelope_with_sender(message_envelope):
    sender = PID()
    sender.address = "test"
    sender.id = "test"
    envelope = message_envelope.with_sender(sender)

    assert message_envelope.message == envelope.message
    assert sender == envelope.sender
    assert message_envelope.header == envelope.header


def test_create_new_message_envelope_with_message(message_envelope):
    message = "test message"
    envelope = message_envelope.with_message(message)

    assert message == envelope.message
    assert message_envelope.sender == envelope.sender
    assert message_envelope.header == envelope.header


def test_create_new_message_envelope_with_header_based_on_key_value_pair_collection(message_envelope):
    collection = {"Test Key": "Test Value", "Test Key 1": "Test Value 1"}
    envelope = message_envelope.with_header(collection)
    assert envelope.header["Test Key"] == "Test Value"


def test_create_new_message_envelope_with_header_based_on_message_header(message_envelope):
    key = "Test Key"
    value = "Test Value"
    message_header = MessageHeader({key: value})
    envelope = message_envelope.with_header(message_header)
    assert envelope.header[key] == value


def test_create_new_message_envelope_with_header_based_on_key_value_pair(message_envelope):
    key = "Test Key"
    value = "Test Value"
    envelope = message_envelope.with_header(key=key, value=value)
    assert envelope.header[key] == value


def test_unwrap(message_envelope):
    message, sender, header = MessageEnvelope.unwrap(message_envelope)
    assert message == message_envelope.message
    assert sender == message_envelope.sender
    assert header == message_envelope.header


def test_unwrap_header(message_envelope):
    assert 0 == len(message_envelope.header)


def test_unwrap_message(message_envelope):
    message = MessageEnvelope.unwrap_message(message_envelope)
    assert message == message_envelope.message


def test_unwrap_sender(message_envelope):
    sender = MessageEnvelope.unwrap_sender(message_envelope)
    assert sender == message_envelope.sender
