# -*- coding: utf-8 -*-
# Copyright 2022 Google LLC
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

from google.cloud.pubsublite_v1.types import admin
from google.cloud.pubsublite_v1.types import common


class ListTopicsPager:
    """A pager for iterating through ``list_topics`` requests.

    This class thinly wraps an initial
    :class:`google.cloud.pubsublite_v1.types.ListTopicsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``topics`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListTopics`` requests and continue to iterate
    through the ``topics`` field on the
    corresponding responses.

    All the usual :class:`google.cloud.pubsublite_v1.types.ListTopicsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., admin.ListTopicsResponse],
        request: admin.ListTopicsRequest,
        response: admin.ListTopicsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.cloud.pubsublite_v1.types.ListTopicsRequest):
                The initial request object.
            response (google.cloud.pubsublite_v1.types.ListTopicsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = admin.ListTopicsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[admin.ListTopicsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[common.Topic]:
        for page in self.pages:
            yield from page.topics

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListTopicsAsyncPager:
    """A pager for iterating through ``list_topics`` requests.

    This class thinly wraps an initial
    :class:`google.cloud.pubsublite_v1.types.ListTopicsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``topics`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListTopics`` requests and continue to iterate
    through the ``topics`` field on the
    corresponding responses.

    All the usual :class:`google.cloud.pubsublite_v1.types.ListTopicsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., Awaitable[admin.ListTopicsResponse]],
        request: admin.ListTopicsRequest,
        response: admin.ListTopicsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.cloud.pubsublite_v1.types.ListTopicsRequest):
                The initial request object.
            response (google.cloud.pubsublite_v1.types.ListTopicsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = admin.ListTopicsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[admin.ListTopicsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response

    def __aiter__(self) -> AsyncIterator[common.Topic]:
        async def async_generator():
            async for page in self.pages:
                for response in page.topics:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListTopicSubscriptionsPager:
    """A pager for iterating through ``list_topic_subscriptions`` requests.

    This class thinly wraps an initial
    :class:`google.cloud.pubsublite_v1.types.ListTopicSubscriptionsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``subscriptions`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListTopicSubscriptions`` requests and continue to iterate
    through the ``subscriptions`` field on the
    corresponding responses.

    All the usual :class:`google.cloud.pubsublite_v1.types.ListTopicSubscriptionsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., admin.ListTopicSubscriptionsResponse],
        request: admin.ListTopicSubscriptionsRequest,
        response: admin.ListTopicSubscriptionsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.cloud.pubsublite_v1.types.ListTopicSubscriptionsRequest):
                The initial request object.
            response (google.cloud.pubsublite_v1.types.ListTopicSubscriptionsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = admin.ListTopicSubscriptionsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[admin.ListTopicSubscriptionsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[str]:
        for page in self.pages:
            yield from page.subscriptions

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListTopicSubscriptionsAsyncPager:
    """A pager for iterating through ``list_topic_subscriptions`` requests.

    This class thinly wraps an initial
    :class:`google.cloud.pubsublite_v1.types.ListTopicSubscriptionsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``subscriptions`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListTopicSubscriptions`` requests and continue to iterate
    through the ``subscriptions`` field on the
    corresponding responses.

    All the usual :class:`google.cloud.pubsublite_v1.types.ListTopicSubscriptionsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., Awaitable[admin.ListTopicSubscriptionsResponse]],
        request: admin.ListTopicSubscriptionsRequest,
        response: admin.ListTopicSubscriptionsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.cloud.pubsublite_v1.types.ListTopicSubscriptionsRequest):
                The initial request object.
            response (google.cloud.pubsublite_v1.types.ListTopicSubscriptionsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = admin.ListTopicSubscriptionsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[admin.ListTopicSubscriptionsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response

    def __aiter__(self) -> AsyncIterator[str]:
        async def async_generator():
            async for page in self.pages:
                for response in page.subscriptions:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListSubscriptionsPager:
    """A pager for iterating through ``list_subscriptions`` requests.

    This class thinly wraps an initial
    :class:`google.cloud.pubsublite_v1.types.ListSubscriptionsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``subscriptions`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListSubscriptions`` requests and continue to iterate
    through the ``subscriptions`` field on the
    corresponding responses.

    All the usual :class:`google.cloud.pubsublite_v1.types.ListSubscriptionsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., admin.ListSubscriptionsResponse],
        request: admin.ListSubscriptionsRequest,
        response: admin.ListSubscriptionsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.cloud.pubsublite_v1.types.ListSubscriptionsRequest):
                The initial request object.
            response (google.cloud.pubsublite_v1.types.ListSubscriptionsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = admin.ListSubscriptionsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[admin.ListSubscriptionsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[common.Subscription]:
        for page in self.pages:
            yield from page.subscriptions

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListSubscriptionsAsyncPager:
    """A pager for iterating through ``list_subscriptions`` requests.

    This class thinly wraps an initial
    :class:`google.cloud.pubsublite_v1.types.ListSubscriptionsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``subscriptions`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListSubscriptions`` requests and continue to iterate
    through the ``subscriptions`` field on the
    corresponding responses.

    All the usual :class:`google.cloud.pubsublite_v1.types.ListSubscriptionsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., Awaitable[admin.ListSubscriptionsResponse]],
        request: admin.ListSubscriptionsRequest,
        response: admin.ListSubscriptionsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.cloud.pubsublite_v1.types.ListSubscriptionsRequest):
                The initial request object.
            response (google.cloud.pubsublite_v1.types.ListSubscriptionsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = admin.ListSubscriptionsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[admin.ListSubscriptionsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response

    def __aiter__(self) -> AsyncIterator[common.Subscription]:
        async def async_generator():
            async for page in self.pages:
                for response in page.subscriptions:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListReservationsPager:
    """A pager for iterating through ``list_reservations`` requests.

    This class thinly wraps an initial
    :class:`google.cloud.pubsublite_v1.types.ListReservationsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``reservations`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListReservations`` requests and continue to iterate
    through the ``reservations`` field on the
    corresponding responses.

    All the usual :class:`google.cloud.pubsublite_v1.types.ListReservationsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., admin.ListReservationsResponse],
        request: admin.ListReservationsRequest,
        response: admin.ListReservationsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.cloud.pubsublite_v1.types.ListReservationsRequest):
                The initial request object.
            response (google.cloud.pubsublite_v1.types.ListReservationsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = admin.ListReservationsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[admin.ListReservationsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[common.Reservation]:
        for page in self.pages:
            yield from page.reservations

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListReservationsAsyncPager:
    """A pager for iterating through ``list_reservations`` requests.

    This class thinly wraps an initial
    :class:`google.cloud.pubsublite_v1.types.ListReservationsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``reservations`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListReservations`` requests and continue to iterate
    through the ``reservations`` field on the
    corresponding responses.

    All the usual :class:`google.cloud.pubsublite_v1.types.ListReservationsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., Awaitable[admin.ListReservationsResponse]],
        request: admin.ListReservationsRequest,
        response: admin.ListReservationsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.cloud.pubsublite_v1.types.ListReservationsRequest):
                The initial request object.
            response (google.cloud.pubsublite_v1.types.ListReservationsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = admin.ListReservationsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[admin.ListReservationsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response

    def __aiter__(self) -> AsyncIterator[common.Reservation]:
        async def async_generator():
            async for page in self.pages:
                for response in page.reservations:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListReservationTopicsPager:
    """A pager for iterating through ``list_reservation_topics`` requests.

    This class thinly wraps an initial
    :class:`google.cloud.pubsublite_v1.types.ListReservationTopicsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``topics`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListReservationTopics`` requests and continue to iterate
    through the ``topics`` field on the
    corresponding responses.

    All the usual :class:`google.cloud.pubsublite_v1.types.ListReservationTopicsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., admin.ListReservationTopicsResponse],
        request: admin.ListReservationTopicsRequest,
        response: admin.ListReservationTopicsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.cloud.pubsublite_v1.types.ListReservationTopicsRequest):
                The initial request object.
            response (google.cloud.pubsublite_v1.types.ListReservationTopicsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = admin.ListReservationTopicsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[admin.ListReservationTopicsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[str]:
        for page in self.pages:
            yield from page.topics

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)


class ListReservationTopicsAsyncPager:
    """A pager for iterating through ``list_reservation_topics`` requests.

    This class thinly wraps an initial
    :class:`google.cloud.pubsublite_v1.types.ListReservationTopicsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``topics`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListReservationTopics`` requests and continue to iterate
    through the ``topics`` field on the
    corresponding responses.

    All the usual :class:`google.cloud.pubsublite_v1.types.ListReservationTopicsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """

    def __init__(
        self,
        method: Callable[..., Awaitable[admin.ListReservationTopicsResponse]],
        request: admin.ListReservationTopicsRequest,
        response: admin.ListReservationTopicsResponse,
        *,
        metadata: Sequence[Tuple[str, str]] = ()
    ):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (google.cloud.pubsublite_v1.types.ListReservationTopicsRequest):
                The initial request object.
            response (google.cloud.pubsublite_v1.types.ListReservationTopicsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = admin.ListReservationTopicsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[admin.ListReservationTopicsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response

    def __aiter__(self) -> AsyncIterator[str]:
        async def async_generator():
            async for page in self.pages:
                for response in page.topics:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return "{0}<{1!r}>".format(self.__class__.__name__, self._response)
