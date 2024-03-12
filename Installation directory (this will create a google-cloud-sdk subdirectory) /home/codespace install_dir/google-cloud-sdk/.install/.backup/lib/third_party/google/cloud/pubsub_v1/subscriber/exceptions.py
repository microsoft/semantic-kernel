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

from enum import Enum
from google.api_core.exceptions import GoogleAPICallError
from typing import Optional


class AcknowledgeStatus(Enum):
    SUCCESS = 1
    PERMISSION_DENIED = 2
    FAILED_PRECONDITION = 3
    INVALID_ACK_ID = 4
    OTHER = 5


class AcknowledgeError(GoogleAPICallError):
    """Error during ack/modack/nack operation on exactly-once-enabled subscription."""

    def __init__(self, error_code: AcknowledgeStatus, info: Optional[str]):
        self.error_code = error_code
        self.info = info
        message = None
        if info:
            message = str(self.error_code) + " : " + str(self.info)
        else:
            message = str(self.error_code)
        super(AcknowledgeError, self).__init__(message)


__all__ = ("AcknowledgeError",)
