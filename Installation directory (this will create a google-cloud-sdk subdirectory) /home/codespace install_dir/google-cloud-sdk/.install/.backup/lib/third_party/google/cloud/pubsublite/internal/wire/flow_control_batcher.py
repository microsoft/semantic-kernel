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

from typing import List, Optional

from google.cloud.pubsublite_v1 import FlowControlRequest, SequencedMessage

_EXPEDITE_BATCH_REQUEST_RATIO = 0.5
_MAX_INT64 = 0x7FFFFFFFFFFFFFFF


def _clamp(val: int):
    if val > _MAX_INT64:
        return _MAX_INT64
    if val < 0:
        return 0
    return val


class _AggregateRequest:
    _request: FlowControlRequest.meta.pb

    def __init__(self):
        self._request = FlowControlRequest.meta.pb()

    def __add__(self, other: FlowControlRequest):
        other_pb = other._pb
        self._request.allowed_bytes = (
            self._request.allowed_bytes + other_pb.allowed_bytes
        )
        self._request.allowed_bytes = min(self._request.allowed_bytes, _MAX_INT64)
        self._request.allowed_messages = (
            self._request.allowed_messages + other_pb.allowed_messages
        )
        self._request.allowed_messages = min(self._request.allowed_messages, _MAX_INT64)
        return self

    def to_optional(self) -> Optional[FlowControlRequest]:
        allowed_messages = _clamp(self._request.allowed_messages)
        allowed_bytes = _clamp(self._request.allowed_bytes)
        if allowed_messages == 0 and allowed_bytes == 0:
            return None
        request = FlowControlRequest()
        request._pb.allowed_messages = allowed_messages
        request._pb.allowed_bytes = allowed_bytes
        return request


def _exceeds_expedite_ratio(pending: int, client: int):
    if client <= 0:
        return False
    return (pending / client) >= _EXPEDITE_BATCH_REQUEST_RATIO


class FlowControlBatcher:
    _client_tokens: _AggregateRequest
    _pending_tokens: _AggregateRequest

    def __init__(self):
        self._client_tokens = _AggregateRequest()
        self._pending_tokens = _AggregateRequest()

    def add(self, request: FlowControlRequest):
        self._client_tokens += request
        self._pending_tokens += request

    def on_messages(self, messages: List[SequencedMessage]):
        byte_size = 0
        for message in messages:
            byte_size += message.size_bytes
        self._client_tokens += FlowControlRequest(
            allowed_bytes=-byte_size, allowed_messages=-len(messages)
        )

    def request_for_restart(self) -> Optional[FlowControlRequest]:
        self._pending_tokens = _AggregateRequest()
        return self._client_tokens.to_optional()

    def release_pending_request(self) -> Optional[FlowControlRequest]:
        request = self._pending_tokens
        self._pending_tokens = _AggregateRequest()
        return request.to_optional()
