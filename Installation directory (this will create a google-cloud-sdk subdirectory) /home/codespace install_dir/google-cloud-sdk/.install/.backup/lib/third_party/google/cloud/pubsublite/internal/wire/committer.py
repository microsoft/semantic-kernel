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

from abc import abstractmethod, ABCMeta
from typing import AsyncContextManager

from google.cloud.pubsublite_v1 import Cursor


class Committer(AsyncContextManager, metaclass=ABCMeta):
    """
    A Committer is able to commit subscribers' completed offsets.
    """

    @abstractmethod
    def commit(self, cursor: Cursor) -> None:
        """
        Start the commit for a cursor.

        Raises:
          GoogleAPICallError: When the committer terminates in failure.
        """
        pass

    @abstractmethod
    async def wait_until_empty(self):
        """
        Flushes pending commits and waits for all outstanding commit responses from the server.

        Raises:
          GoogleAPICallError: When the committer terminates in failure.
        """
        pass
