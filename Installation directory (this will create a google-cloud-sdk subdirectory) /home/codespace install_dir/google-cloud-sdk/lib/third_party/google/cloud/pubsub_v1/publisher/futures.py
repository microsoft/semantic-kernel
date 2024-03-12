# Copyright 2019, Google LLC All rights reserved.
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
from typing import Any, Callable, Union

from google.cloud.pubsub_v1 import futures

if typing.TYPE_CHECKING:  # pragma: NO COVER
    from google.cloud import pubsub_v1


class Future(futures.Future):
    """This future object is returned from asychronous Pub/Sub publishing
    calls.

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

    def result(self, timeout: Union[int, float] = None) -> str:
        """Return the message ID or raise an exception.

        This blocks until the message has been published successfully and
        returns the message ID unless an exception is raised.

        Args:
            timeout: The number of seconds before this call
                times out and raises TimeoutError.

        Returns:
            The message ID.

        Raises:
            concurrent.futures.TimeoutError: If the request times out.
            Exception: For undefined exceptions in the underlying
                call execution.
        """
        return super().result(timeout=timeout)

    # This exists to make the type checkers happy.
    def add_done_callback(
        self, callback: Callable[["pubsub_v1.publisher.futures.Future"], Any]
    ) -> None:
        """Attach a callable that will be called when the future finishes.

        Args:
            callback:
                A callable that will be called with this future as its only
                argument when the future completes or is cancelled. The callable
                will always be called by a thread in the same process in which
                it was added. If the future has already completed or been
                cancelled then the callable will be called immediately. These
                callables are called in the order that they were added.
        """
        return super().add_done_callback(callback)  # type: ignore
