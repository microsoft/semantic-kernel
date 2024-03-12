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

import typing
from typing import Any
from typing import Union

from google.cloud.pubsub_v1 import futures
from google.cloud.pubsub_v1.subscriber.exceptions import AcknowledgeStatus

if typing.TYPE_CHECKING:  # pragma: NO COVER
    from google.cloud.pubsub_v1.subscriber._protocol.streaming_pull_manager import (
        StreamingPullManager,
    )


class StreamingPullFuture(futures.Future):
    """Represents a process that asynchronously performs streaming pull and
    schedules messages to be processed.

    This future is resolved when the process is stopped (via :meth:`cancel`) or
    if it encounters an unrecoverable error. Calling `.result()` will cause
    the calling thread to block indefinitely.
    """

    def __init__(self, manager: "StreamingPullManager"):
        super(StreamingPullFuture, self).__init__()
        self.__manager = manager
        self.__manager.add_close_callback(self._on_close_callback)
        self.__cancelled = False

    def _on_close_callback(self, manager: "StreamingPullManager", result: Any):
        if self.done():
            # The future has already been resolved in a different thread,
            # nothing to do on the streaming pull manager shutdown.
            return

        if result is None:
            self.set_result(True)
        else:
            self.set_exception(result)

    def cancel(self) -> bool:
        """Stops pulling messages and shutdowns the background thread consuming
        messages.

        The method always returns ``True``, as the shutdown is always initiated.
        However, if the background stream is already being shut down or the shutdown
        has completed, this method is a no-op.

        .. versionchanged:: 2.4.1
           The method does not block anymore, it just triggers the shutdown and returns
           immediately. To block until the background stream is terminated, call
           :meth:`result()` after cancelling the future.

        .. versionchanged:: 2.10.0
           The method always returns ``True`` instead of ``None``.
        """
        # NOTE: We circumvent the base future's self._state to track the cancellation
        # state, as this state has different meaning with streaming pull futures.
        self.__cancelled = True
        self.__manager.close()
        return True

    def cancelled(self) -> bool:
        """
        Returns:
            ``True`` if the subscription has been cancelled.
        """
        return self.__cancelled


class Future(futures.Future):
    """This future object is for subscribe-side calls.

    Calling :meth:`result` will resolve the future by returning the message
    ID, unless an error occurs.
    """

    def cancel(self) -> bool:
        """Actions in Pub/Sub generally may not be canceled.

        This method always returns ``False``.
        """
        return False

    def cancelled(self) -> bool:
        """Actions in Pub/Sub generally may not be canceled.

        This method always returns ``False``.
        """
        return False

    def result(self, timeout: Union[int, float] = None) -> AcknowledgeStatus:
        """Return a success code or raise an exception.

        This blocks until the operation completes successfully and
        returns the error code unless an exception is raised.

        Args:
            timeout: The number of seconds before this call
                times out and raises TimeoutError.

        Returns:
            AcknowledgeStatus.SUCCESS if the operation succeeded.

        Raises:
            concurrent.futures.TimeoutError: If the request times out.
            AcknowledgeError: If the operation did not succeed for another
                reason.
        """
        return super().result(timeout=timeout)
