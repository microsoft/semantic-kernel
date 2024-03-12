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

from grpc import StatusCode
from google.api_core.exceptions import GoogleAPICallError

retryable_codes = {
    StatusCode.DEADLINE_EXCEEDED,
    StatusCode.ABORTED,
    StatusCode.INTERNAL,
    StatusCode.UNAVAILABLE,
    StatusCode.UNKNOWN,
    StatusCode.CANCELLED,
}


def is_retryable(error: GoogleAPICallError) -> bool:
    return error.grpc_status_code in retryable_codes
