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

from unittest.mock import MagicMock
from google.api_core.exceptions import Aborted, GoogleAPICallError
from cloudsdk.google.protobuf.any_pb2 import Any  # pytype: disable=pyi-error
from google.rpc.error_details_pb2 import ErrorInfo
from google.rpc.status_pb2 import Status
import grpc
from grpc_status import rpc_status


def make_call(status_pb: Status) -> grpc.Call:
    status = rpc_status.to_status(status_pb)
    mock_call = MagicMock(spec=grpc.Call)
    mock_call.details.return_value = status.details
    mock_call.code.return_value = status.code
    mock_call.trailing_metadata.return_value = status.trailing_metadata
    return mock_call


def make_call_without_metadata(status_pb: Status) -> grpc.Call:
    mock_call = make_call(status_pb)
    # Causes rpc_status.from_call to return None.
    mock_call.trailing_metadata.return_value = None
    return mock_call


def make_reset_signal() -> GoogleAPICallError:
    any = Any()
    any.Pack(ErrorInfo(reason="RESET", domain="pubsublite.googleapis.com"))
    status_pb = Status(code=10, details=[any])
    return Aborted("", response=make_call(status_pb))
