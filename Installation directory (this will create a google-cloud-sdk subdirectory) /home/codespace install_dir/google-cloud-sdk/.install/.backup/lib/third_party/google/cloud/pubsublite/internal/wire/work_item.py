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

import asyncio
from typing import Generic

from google.cloud.pubsublite.internal.wire.connection import Request, Response


class WorkItem(Generic[Request, Response]):
    """An item of work and a future to complete when it is finished."""

    request: Request
    response_future: "asyncio.Future[Response]"

    def __init__(self, request: Request):
        self.request = request
        self.response_future = asyncio.Future()
