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

import concurrent.futures
from typing import Any, NoReturn, Optional

import google.api_core.future


class Future(concurrent.futures.Future, google.api_core.future.Future):
    """Encapsulation of the asynchronous execution of an action.

    This object is returned from asychronous Pub/Sub calls, and is the
    interface to determine the status of those calls.

    This object should not be created directly, but is returned by other
    methods in this library.
    """

    def running(self) -> bool:
        """Return ``True`` if the associated Pub/Sub action has not yet completed."""
        return not self.done()

    def set_running_or_notify_cancel(self) -> NoReturn:
        raise NotImplementedError(
            "Only used by executors from `concurrent.futures` package."
        )

    def set_result(self, result: Any):
        """Set the return value of work associated with the future.

        Do not use this method, it should only be used internally by the library and its
        unit tests.
        """
        return super().set_result(result=result)

    def set_exception(self, exception: Optional[BaseException]):
        """Set the result of the future as being the given exception.

        Do not use this method, it should only be used internally by the library and its
        unit tests.
        """
        return super().set_exception(exception=exception)
