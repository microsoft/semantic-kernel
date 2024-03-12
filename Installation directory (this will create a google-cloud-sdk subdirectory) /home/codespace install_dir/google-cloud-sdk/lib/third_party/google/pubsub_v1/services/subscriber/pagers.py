# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
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
#
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Sequence,
    Tuple,
    Optional,
    Iterator,
)

from google.pubsub_v1.types import pubsub


class ListSubscriptionsPager:
    """A pager for iterating through ``list_subscriptions`` requests.

    This class thinly wraps an initial
    :class:`google.pubsub_v1.types.ListSubscriptionsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``subscriptions`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListSubscriptions`` requests and continue to iterate
    through the ``subscriptions`` field on the
    corresponding responses.

    All the usual :class:`google.pubsub_v1.types.ListSubscriptionsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., pubsub.ListSubscriptionsResponse],
        request: pubsub.ListSubscriptionsRequest,
        response: pubsub.ListSubscriptionsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.pubsub_v1.types.ListSubscriptionsRequest):
                The initial request object.
            response (google.pubsub_v1.types.ListSubscriptionsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = pubsub.ListSubscriptionsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[pubsub.ListSubscriptionsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[pubsub.Subscription]:
        for page in self.pages:
            yield from page.subscriptions

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListSubscriptionsAsyncPager:
    """A pager for iterating through ``list_subscriptions`` requests.

    This class thinly wraps an initial
    :class:`google.pubsub_v1.types.ListSubscriptionsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``subscriptions`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListSubscriptions`` requests and continue to iterate
    through the ``subscriptions`` field on the
    corresponding responses.

    All the usual :class:`google.pubsub_v1.types.ListSubscriptionsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., Awaitable[pubsub.ListSubscriptionsResponse]],
        request: pubsub.ListSubscriptionsRequest,
        response: pubsub.ListSubscriptionsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.pubsub_v1.types.ListSubscriptionsRequest):
                The initial request object.
            response (google.pubsub_v1.types.ListSubscriptionsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = pubsub.ListSubscriptionsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[pubsub.ListSubscriptionsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response

    def __aiter__(self) -> AsyncIterator[pubsub.Subscription]:
        async def async_generator():
            async for page in self.pages:
                for response in page.subscriptions:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListSnapshotsPager:
    """A pager for iterating through ``list_snapshots`` requests.

    This class thinly wraps an initial
    :class:`google.pubsub_v1.types.ListSnapshotsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``snapshots`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListSnapshots`` requests and continue to iterate
    through the ``snapshots`` field on the
    corresponding responses.

    All the usual :class:`google.pubsub_v1.types.ListSnapshotsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., pubsub.ListSnapshotsResponse],
        request: pubsub.ListSnapshotsRequest,
        response: pubsub.ListSnapshotsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.pubsub_v1.types.ListSnapshotsRequest):
                The initial request object.
            response (google.pubsub_v1.types.ListSnapshotsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = pubsub.ListSnapshotsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[pubsub.ListSnapshotsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[pubsub.Snapshot]:
        for page in self.pages:
            yield from page.snapshots

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListSnapshotsAsyncPager:
    """A pager for iterating through ``list_snapshots`` requests.

    This class thinly wraps an initial
    :class:`google.pubsub_v1.types.ListSnapshotsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``snapshots`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListSnapshots`` requests and continue to iterate
    through the ``snapshots`` field on the
    corresponding responses.

    All the usual :class:`google.pubsub_v1.types.ListSnapshotsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., Awaitable[pubsub.ListSnapshotsResponse]],
        request: pubsub.ListSnapshotsRequest,
        response: pubsub.ListSnapshotsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.pubsub_v1.types.ListSnapshotsRequest):
                The initial request object.
            response (google.pubsub_v1.types.ListSnapshotsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = pubsub.ListSnapshotsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[pubsub.ListSnapshotsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response

    def __aiter__(self) -> AsyncIterator[pubsub.Snapshot]:
        async def async_generator():
            async for page in self.pages:
                for response in page.snapshots:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)
