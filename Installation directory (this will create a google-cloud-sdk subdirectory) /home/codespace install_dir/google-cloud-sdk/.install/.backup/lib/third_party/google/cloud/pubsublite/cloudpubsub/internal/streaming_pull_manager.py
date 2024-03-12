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

from abc import ABC, abstractmethod
from typing import Optional, Callable

from google.api_core.exceptions import GoogleAPICallError


CloseCallback = Callable[["StreamingPullManager", Optional[GoogleAPICallError]], None]


class StreamingPullManager(ABC):
    """The API expected by StreamingPullFuture."""

    @abstractmethod
    def add_close_callback(self, close_callback: CloseCallback):
        pass

    @abstractmethod
    def close(self):
        pass
