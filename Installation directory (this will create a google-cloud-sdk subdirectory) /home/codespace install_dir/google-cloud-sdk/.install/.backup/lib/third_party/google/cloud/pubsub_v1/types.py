# Copyright 2017, Google LLC All rights reserved.
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

from __future__ import absolute_import

import collections
import enum
import inspect
import sys
import typing
from typing import Dict, NamedTuple, Union

import proto  # type: ignore

from google.api import http_pb2  # type: ignore
from google.api_core import gapic_v1
from google.iam.v1 import iam_policy_pb2  # type: ignore
from google.iam.v1 import policy_pb2
from google.iam.v1.logging import audit_data_pb2  # type: ignore
from cloudsdk.google.protobuf import descriptor_pb2
from cloudsdk.google.protobuf import duration_pb2
from cloudsdk.google.protobuf import empty_pb2
from cloudsdk.google.protobuf import field_mask_pb2
from cloudsdk.google.protobuf import timestamp_pb2

from google.api_core.protobuf_helpers import get_messages

from google.pubsub_v1.types import pubsub as pubsub_gapic_types


if typing.TYPE_CHECKING:  # pragma: NO COVER
    from types import ModuleType
    from google.pubsub_v1 import types as gapic_types
    from google.pubsub_v1.services.publisher.client import OptionalRetry

    # TODO: Eventually implement OptionalTimeout in the GAPIC code generator and import
    # it from the generated code. It's the same solution that is used for OptionalRetry.
    # https://github.com/googleapis/gapic-generator-python/pull/1032/files
    # https://github.com/googleapis/gapic-generator-python/pull/1065/files
    if hasattr(gapic_v1.method, "_MethodDefault"):
        # _MethodDefault was only added in google-api-core==2.2.2
        OptionalTimeout = Union[gapic_types.TimeoutType, gapic_v1.method._MethodDefault]
    else:
        OptionalTimeout = Union[gapic_types.TimeoutType, object]  # type: ignore


# Define the default values for batching.
#
# This class is used when creating a publisher or subscriber client, and
# these settings can be altered to tweak Pub/Sub behavior.
# The defaults should be fine for most use cases.
class BatchSettings(NamedTuple):
    """The settings for batch publishing the messages.

    Attributes:
        max_bytes (int):
            The maximum total size of the messages to collect before automatically
            publishing the batch, including any byte size overhead of the publish
            request itself. The maximum value is bound by the server-side limit of
            10_000_000 bytes. Defaults to 1 MB.
        max_latency (float):
            The maximum number of seconds to wait for additional messages before
            automatically publishing the batch. Defaults to 10ms.
        max_messages (int):
            The maximum number of messages to collect before automatically
            publishing the batch. Defaults to 100.
    """

    max_bytes: int = 1 * 1000 * 1000  # 1 MB
    (
        "The maximum total size of the messages to collect before automatically "
        "publishing the batch, including any byte size overhead of the publish "
        "request itself. The maximum value is bound by the server-side limit of "
        "10_000_000 bytes."
    )

    max_latency: float = 0.01  # 10 ms
    (
        "The maximum number of seconds to wait for additional messages before "
        "automatically publishing the batch."
    )

    max_messages: int = 100
    (
        "The maximum number of messages to collect before automatically "
        "publishing the batch."
    )


class LimitExceededBehavior(str, enum.Enum):
    """The possible actions when exceeding the publish flow control limits."""

    IGNORE = "ignore"
    BLOCK = "block"
    ERROR = "error"


class PublishFlowControl(NamedTuple):
    """The client flow control settings for message publishing.

    Attributes:
        message_limit (int):
            The maximum number of messages awaiting to be published.
            Defaults to 1000.
        byte_limit (int):
            The maximum total size of messages awaiting to be published.
            Defaults to 10MB.
        limit_exceeded_behavior (LimitExceededBehavior):
            The action to take when publish flow control limits are exceeded.
            Defaults to LimitExceededBehavior.IGNORE.
    """

    message_limit: int = 10 * BatchSettings.__new__.__defaults__[2]  # type: ignore
    """The maximum number of messages awaiting to be published."""

    byte_limit: int = 10 * BatchSettings.__new__.__defaults__[0]  # type: ignore
    """The maximum total size of messages awaiting to be published."""

    limit_exceeded_behavior: LimitExceededBehavior = LimitExceededBehavior.IGNORE
    """The action to take when publish flow control limits are exceeded."""


# Define the default publisher options.
#
# This class is used when creating a publisher client to pass in options
# to enable/disable features.
class PublisherOptions(NamedTuple):
    """The options for the publisher client.

    Attributes:
        enable_message_ordering (bool):
            Whether to order messages in a batch by a supplied ordering key.
            Defaults to false.
        flow_control (PublishFlowControl):
            Flow control settings for message publishing by the client. By default
            the publisher client does not do any throttling.
        retry (OptionalRetry):
            Retry settings for message publishing by the client. This should be
            an instance of :class:`google.api_core.retry.Retry`.
        timeout (OptionalTimeout):
            Timeout settings for message publishing by the client. It should be
            compatible with :class:`~.pubsub_v1.types.TimeoutType`.
    """

    enable_message_ordering: bool = False
    """Whether to order messages in a batch by a supplied ordering key."""

    flow_control: PublishFlowControl = PublishFlowControl()
    (
        "Flow control settings for message publishing by the client. By default "
        "the publisher client does not do any throttling."
    )

    retry: "OptionalRetry" = gapic_v1.method.DEFAULT  # use api_core default
    (
        "Retry settings for message publishing by the client. This should be "
        "an instance of :class:`google.api_core.retry.Retry`."
    )

    timeout: "OptionalTimeout" = gapic_v1.method.DEFAULT  # use api_core default
    (
        "Timeout settings for message publishing by the client. It should be "
        "compatible with :class:`~.pubsub_v1.types.TimeoutType`."
    )


# Define the type class and default values for flow control settings.
#
# This class is used when creating a publisher or subscriber client, and
# these settings can be altered to tweak Pub/Sub behavior.
# The defaults should be fine for most use cases.
class FlowControl(NamedTuple):
    """The settings for controlling the rate at which messages are pulled
    with an asynchronous subscription.

    Attributes:
        max_bytes (int):
            The maximum total size of received - but not yet processed - messages
            before pausing the message stream. Defaults to 100 MiB.
        max_messages (int):
            The maximum number of received - but not yet processed - messages before
            pausing the message stream. Defaults to 1000.
        max_lease_duration (float):
            The maximum amount of time in seconds to hold a lease on a message
            before dropping it from the lease management. Defaults to 1 hour.
        min_duration_per_lease_extension (float):
            The min amount of time in seconds for a single lease extension attempt.
            Must be between 10 and 600 (inclusive). Ignored by default, but set to
            60 seconds if the subscription has exactly-once delivery enabled.
        max_duration_per_lease_extension (float):
            The max amount of time in seconds for a single lease extension attempt.
            Bounds the delay before a message redelivery if the subscriber
            fails to extend the deadline. Must be between 10 and 600 (inclusive). Ignored
            if set to 0.
    """

    max_bytes: int = 100 * 1024 * 1024  # 100 MiB
    (
        "The maximum total size of received - but not yet processed - messages "
        "before pausing the message stream."
    )

    max_messages: int = 1000
    (
        "The maximum number of received - but not yet processed - messages before "
        "pausing the message stream."
    )

    max_lease_duration: float = 1 * 60 * 60  # 1 hour
    (
        "The maximum amount of time in seconds to hold a lease on a message "
        "before dropping it from the lease management."
    )

    min_duration_per_lease_extension: float = 0
    (
        "The min amount of time in seconds for a single lease extension attempt. "
        "Must be between 10 and 600 (inclusive). Ignored by default, but set to "
        "60 seconds if the subscription has exactly-once delivery enabled."
    )

    max_duration_per_lease_extension: float = 0  # disabled by default
    (
        "The max amount of time in seconds for a single lease extension attempt. "
        "Bounds the delay before a message redelivery if the subscriber "
        "fails to extend the deadline. Must be between 10 and 600 (inclusive). Ignored "
        "if set to 0."
    )


# The current api core helper does not find new proto messages of type proto.Message,
# thus we need our own helper. Adjusted from
# https://github.com/googleapis/python-api-core/blob/8595f620e7d8295b6a379d6fd7979af3bef717e2/google/api_core/protobuf_helpers.py#L101-L118
def _get_protobuf_messages(module: "ModuleType") -> Dict[str, proto.Message]:
    """Discover all protobuf Message classes in a given import module.

    Args:
        module (module): A Python module; :func:`dir` will be run against this
            module to find Message subclasses.

    Returns:
        dict[str, proto.Message]: A dictionary with the
            Message class names as keys, and the Message subclasses themselves
            as values.
    """
    answer = collections.OrderedDict()
    for name in dir(module):
        candidate = getattr(module, name)
        if inspect.isclass(candidate) and issubclass(candidate, proto.Message):
            answer[name] = candidate
    return answer


_shared_modules = [
    http_pb2,
    iam_policy_pb2,
    policy_pb2,
    audit_data_pb2,
    descriptor_pb2,
    duration_pb2,
    empty_pb2,
    field_mask_pb2,
    timestamp_pb2,
]

_local_modules = [pubsub_gapic_types]

names = [
    "BatchSettings",
    "LimitExceededBehavior",
    "PublishFlowControl",
    "PublisherOptions",
    "FlowControl",
]

for module in _shared_modules:
    for name, message in get_messages(module).items():
        setattr(sys.modules[__name__], name, message)
        names.append(name)

for module in _local_modules:
    for name, message in _get_protobuf_messages(module).items():
        message.__module__ = "google.cloud.pubsub_v1.types"
        setattr(sys.modules[__name__], name, message)
        names.append(name)


__all__ = tuple(sorted(names))
