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


class AckSetTracker(AsyncContextManager, metaclass=ABCMeta):
    """
    An AckSetTracker tracks disjoint acknowledged messages and commits them when a contiguous prefix of tracked offsets
    is aggregated.
    """

    @abstractmethod
    def track(self, offset: int):
        """
        Track the provided offset.

        Args:
          offset: the offset to track.

        Raises:
          GoogleAPICallError: On an invalid offset to track.
        """

    @abstractmethod
    def ack(self, offset: int):
        """
        Acknowledge the message with the provided offset. The offset must have previously been tracked.

        Args:
          offset: the offset to acknowledge.

        Returns:
          GoogleAPICallError: On a commit failure.
        """

    @abstractmethod
    async def clear_and_commit(self):
        """
        Discard all outstanding acks and wait for the commit offset to be acknowledged by the server.

        Raises:
          GoogleAPICallError: If the committer has shut down due to a permanent error.
        """
