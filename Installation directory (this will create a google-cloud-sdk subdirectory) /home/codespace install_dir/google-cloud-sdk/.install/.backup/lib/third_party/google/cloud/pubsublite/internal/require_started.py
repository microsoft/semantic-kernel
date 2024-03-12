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

from typing import ContextManager

from google.api_core.exceptions import FailedPrecondition


class RequireStarted(ContextManager):
    def __init__(self):
        self._started = False

    def __enter__(self):
        if self._started:
            raise FailedPrecondition("__enter__ called twice.")
        self._started = True
        return self

    def require_started(self):
        if not self._started:
            raise FailedPrecondition("__enter__ has never been called.")

    def __exit__(self, exc_type, exc_value, traceback):
        self.require_started()
