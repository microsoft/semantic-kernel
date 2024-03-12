# Copyright 2021 Google LLC
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

from google.api_core.exceptions import GoogleAPICallError
from google.cloud.pubsublite.internal.status_codes import is_retryable
from google.rpc.error_details_pb2 import ErrorInfo
from google.rpc import status_pb2


def is_reset_signal(error: GoogleAPICallError) -> bool:
    """
    Determines whether the given error contains the stream RESET signal, sent by
    the server to instruct clients to reset stream state.

    Returns: True if the error contains the RESET signal.
    """
    if not is_retryable(error) or not error.response:
        return False
    call = error.response
    if call.trailing_metadata() is None:
        return False
    for key, value in call.trailing_metadata():
        if key == "grpc-status-details-bin":
            rich_status = status_pb2.Status.FromString(value)
            if (
                call.code().value[0] != rich_status.code
                or call.details() != rich_status.message
            ):
                return False
            for detail in rich_status.details:
                if detail.Is(ErrorInfo.DESCRIPTOR):
                    info = ErrorInfo()
                    if (
                        detail.Unpack(info)
                        and info.reason == "RESET"
                        and info.domain == "pubsublite.googleapis.com"
                    ):
                        return True
    return False
