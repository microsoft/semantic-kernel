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

from typing import Generic, TypeVar, AsyncContextManager
from abc import abstractmethod, ABCMeta

Request = TypeVar("Request")
Response = TypeVar("Response")


class Connection(
    AsyncContextManager["Connection"], Generic[Request, Response], metaclass=ABCMeta
):
    """
    A connection to an underlying stream. Only one call to 'read' may be outstanding at a time.
    """

    @abstractmethod
    async def write(self, request: Request) -> None:
        """
        Write a message to the stream.

        Raises:
          GoogleAPICallError: When the connection terminates in failure.
        """
        raise NotImplementedError()

    @abstractmethod
    async def read(self) -> Response:
        """
        Read a message off of the stream.

        Raises:
          GoogleAPICallError: When the connection terminates in failure.
        """
        raise NotImplementedError()


class ConnectionFactory(Generic[Request, Response], metaclass=ABCMeta):
    """A factory for producing Connections."""

    @abstractmethod
    async def new(self) -> Connection[Request, Response]:
        raise NotImplementedError()
