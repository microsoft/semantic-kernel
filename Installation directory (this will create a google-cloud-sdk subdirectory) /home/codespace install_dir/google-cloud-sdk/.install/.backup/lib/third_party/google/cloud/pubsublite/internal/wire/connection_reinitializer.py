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

from typing import Generic
from abc import ABCMeta, abstractmethod
from google.api_core.exceptions import GoogleAPICallError
from google.cloud.pubsublite.internal.wire.connection import (
    Connection,
    Request,
    Response,
)


class ConnectionReinitializer(Generic[Request, Response], metaclass=ABCMeta):
    """A class capable of reinitializing a connection after a new one has been created."""

    @abstractmethod
    async def stop_processing(self, error: GoogleAPICallError):
        """Tear down internal state processing the current connection in
        response to a stream error.

        Args:
            error: The error that caused the stream to break
        """
        raise NotImplementedError()

    @abstractmethod
    async def reinitialize(
        self,
        connection: Connection[Request, Response],
    ):
        """Reinitialize a connection. Must ensure no calls to the associated RetryingConnection
        occur until this completes.

        Args:
            connection: The connection to reinitialize

        Raises:
            GoogleAPICallError: If it fails to reinitialize.
        """
        raise NotImplementedError()
