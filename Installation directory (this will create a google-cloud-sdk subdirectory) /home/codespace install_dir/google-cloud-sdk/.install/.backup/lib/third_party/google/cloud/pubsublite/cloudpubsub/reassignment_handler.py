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
from typing import Set, Optional, Awaitable

from google.cloud.pubsublite.types import Partition


class ReassignmentHandler(ABC):
    """
    A ReassignmentHandler is called any time a new partition assignment is received from the server.
    It will be called with both the previous and new assignments as decided by the backend.

    The client library will not acknowledge the assignment until handleReassignment returns. The
    assigning backend will not assign any of the partitions in `before` to another server unless the
    assignment is acknowledged, or a client takes too long to acknowledged (currently 30 seconds from
    the time the assignment is sent from server's point of view).

    Because of the above, as long as reassignment handling is processed quickly, it can be used to
    abort outstanding operations on partitions which are being assigned away from this client.
    """

    @abstractmethod
    def handle_reassignment(
        self, before: Set[Partition], after: Set[Partition]
    ) -> Optional[Awaitable]:
        """
        Called with the previous and new assignment delivered to this client on an assignment change.
        The assignment will not be acknowledged until this method returns, so it should complete
        quickly, or the backend will assume it is non-responsive and assign all partitions away without
        waiting for acknowledgement.

        handle_reassignment will only be called after no new message deliveries will be started for the partition.
        There may still be messages in flight on executors or in async callbacks.

        Acks or nacks on messages from partitions being assigned away will have no effect.

        This method will be called on an event loop and should not block.

        Args:
          before: The previous assignment.
          after: The new assignment.

        Returns:
          Either None or an Awaitable to be waited on before acknowledging reassignment.

        Raises:
          GoogleAPICallError: To fail the client if raised.
        """
        pass


class DefaultReassignmentHandler(ReassignmentHandler):
    def handle_reassignment(
        self, before: Set[Partition], after: Set[Partition]
    ) -> Optional[Awaitable]:
        return None
