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

from google.api_core.exceptions import GoogleAPICallError
from google.cloud.pubsub_v1.exceptions import TimeoutError


class PublishError(GoogleAPICallError):
    pass


class MessageTooLargeError(ValueError):
    """Attempt to publish a message that would exceed the server max size limit."""


class PublishToPausedOrderingKeyException(Exception):
    """Publish attempted to paused ordering key. To resume publishing, call
    the resumePublish method on the publisher Client object with this
    ordering key. Ordering keys are paused if an unrecoverable error
    occurred during publish of a batch for that key.
    """

    def __init__(self, ordering_key: str):
        self.ordering_key = ordering_key
        super(PublishToPausedOrderingKeyException, self).__init__()


class FlowControlLimitError(Exception):
    """An action resulted in exceeding the flow control limits."""


__all__ = (
    "FlowControlLimitError",
    "MessageTooLargeError",
    "PublishError",
    "TimeoutError",
    "PublishToPausedOrderingKeyException",
)
