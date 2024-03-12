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

import threading
from typing import Generic, TypeVar, Callable, Optional

_Client = TypeVar("_Client")
_MAX_CLIENT_USES = 75  # GRPC channels are limited to 100 concurrent streams.


class ClientCache(Generic[_Client]):
    _ClientFactory = Callable[[], _Client]

    _factory: _ClientFactory
    _latest: Optional[_Client]
    _remaining_uses: int
    _lock: threading.Lock

    def __init__(self, factory: _ClientFactory):
        self._factory = factory
        self._latest = None
        self._remaining_uses = 0
        self._lock = threading.Lock()

    def get(self) -> _Client:
        with self._lock:
            if self._remaining_uses <= 0:
                self._remaining_uses = _MAX_CLIENT_USES
                self._latest = self._factory()
            self._remaining_uses -= 1
            return self._latest
