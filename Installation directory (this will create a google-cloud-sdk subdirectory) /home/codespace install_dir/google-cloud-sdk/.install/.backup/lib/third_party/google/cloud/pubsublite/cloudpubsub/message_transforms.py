# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime

from google.api_core.exceptions import InvalidArgument
from cloudsdk.google.protobuf.timestamp_pb2 import Timestamp  # pytype: disable=pyi-error
from google.pubsub_v1 import PubsubMessage

from google.cloud.pubsublite.cloudpubsub import MessageTransformer
from google.cloud.pubsublite.internal import fast_serialize
from google.cloud.pubsublite.types import Partition, MessageMetadata
from google.cloud.pubsublite_v1 import AttributeValues, SequencedMessage, PubSubMessage

PUBSUB_LITE_EVENT_TIME = "x-goog-pubsublite-event-time"


def _encode_attribute_event_time_proto(ts: Timestamp) -> str:
    return fast_serialize.dump([ts.seconds, ts.nanos])


def _decode_attribute_event_time_proto(attr: str) -> Timestamp:
    try:
        ts = Timestamp()
        loaded = fast_serialize.load(attr)
        ts.seconds = loaded[0]
        ts.nanos = loaded[1]
        return ts
    except Exception:  # noqa: E722
        raise InvalidArgument("Invalid value for event time attribute.")


def encode_attribute_event_time(dt: datetime.datetime) -> str:
    ts = Timestamp()
    ts.FromDatetime(dt.astimezone(datetime.timezone.utc))
    return _encode_attribute_event_time_proto(ts)


def decode_attribute_event_time(attr: str) -> datetime.datetime:
    return (
        _decode_attribute_event_time_proto(attr)
        .ToDatetime()
        .replace(tzinfo=datetime.timezone.utc)
    )


def _parse_attributes(values: AttributeValues) -> str:
    if not len(values.values) == 1:
        raise InvalidArgument(
            "Received an unparseable message with multiple values for an attribute."
        )
    value: bytes = values.values[0]
    try:
        return value.decode("utf-8")
    except UnicodeError:
        raise InvalidArgument(
            "Received an unparseable message with a non-utf8 attribute."
        )


def add_id_to_cps_subscribe_transformer(
    partition: Partition, transformer: MessageTransformer
) -> MessageTransformer:
    def add_id_to_message(source: SequencedMessage):
        source_pb = source._pb
        message: PubsubMessage = transformer.transform(source)
        message_pb = message._pb
        if message_pb.message_id:
            raise InvalidArgument(
                "Message after transforming has the message_id field set."
            )
        message_pb.message_id = MessageMetadata._encode_parts(
            partition.value, source_pb.cursor.offset
        )
        return message

    return MessageTransformer.of_callable(add_id_to_message)


def to_cps_subscribe_message(source: SequencedMessage) -> PubsubMessage:
    source_pb = source._pb
    out_pb = _to_cps_publish_message_proto(source_pb.message)
    out_pb.publish_time.CopyFrom(source_pb.publish_time)
    out = PubsubMessage()
    out._pb = out_pb
    return out


def _to_cps_publish_message_proto(
    source: PubSubMessage.meta.pb,
) -> PubsubMessage.meta.pb:
    out = PubsubMessage.meta.pb()
    try:
        out.ordering_key = source.key.decode("utf-8")
    except UnicodeError:
        raise InvalidArgument("Received an unparseable message with a non-utf8 key.")
    if PUBSUB_LITE_EVENT_TIME in source.attributes:
        raise InvalidArgument(
            "Special timestamp attribute exists in wire message. Unable to parse message."
        )
    out.data = source.data
    for key, values in source.attributes.items():
        out.attributes[key] = _parse_attributes(values)
    if source.HasField("event_time"):
        out.attributes[PUBSUB_LITE_EVENT_TIME] = _encode_attribute_event_time_proto(
            source.event_time
        )
    return out


def to_cps_publish_message(source: PubSubMessage) -> PubsubMessage:
    out = PubsubMessage()
    out._pb = _to_cps_publish_message_proto(source._pb)
    return out


def from_cps_publish_message(source: PubsubMessage) -> PubSubMessage:
    source_pb = source._pb
    out = PubSubMessage()
    out_pb = out._pb
    if PUBSUB_LITE_EVENT_TIME in source_pb.attributes:
        out_pb.event_time.CopyFrom(
            _decode_attribute_event_time_proto(
                source_pb.attributes[PUBSUB_LITE_EVENT_TIME]
            )
        )
    out_pb.data = source_pb.data
    out_pb.key = source_pb.ordering_key.encode("utf-8")
    for key, value in source_pb.attributes.items():
        if key != PUBSUB_LITE_EVENT_TIME:
            out_pb.attributes[key].values.append(value.encode("utf-8"))
    return out
