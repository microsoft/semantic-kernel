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

import typing
from typing import NamedTuple, Optional

if typing.TYPE_CHECKING:  # pragma: NO COVER
    from google.cloud.pubsub_v1.subscriber import futures


# Namedtuples for management requests. Used by the Message class to communicate
# items of work back to the policy.
class AckRequest(NamedTuple):
    ack_id: str
    byte_size: int
    time_to_ack: float
    ordering_key: Optional[str]
    future: Optional["futures.Future"]


class DropRequest(NamedTuple):
    ack_id: str
    byte_size: int
    ordering_key: Optional[str]


class LeaseRequest(NamedTuple):
    ack_id: str
    byte_size: int
    ordering_key: Optional[str]


class ModAckRequest(NamedTuple):
    ack_id: str
    seconds: float
    future: Optional["futures.Future"]


class NackRequest(NamedTuple):
    ack_id: str
    byte_size: int
    ordering_key: Optional[str]
    future: Optional["futures.Future"]
