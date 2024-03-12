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
from typing import Any, AsyncIterator, Awaitable, Callable, Sequence, Tuple, Optional, Iterator

from googlecloudsdk.generated_clients.gapic_clients.logging_v2.types import logging_config


class ListBucketsPager:
    """A pager for iterating through ``list_buckets`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListBucketsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``buckets`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListBuckets`` requests and continue to iterate
    through the ``buckets`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListBucketsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., logging_config.ListBucketsResponse],
            request: logging_config.ListBucketsRequest,
            response: logging_config.ListBucketsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListBucketsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListBucketsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListBucketsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[logging_config.ListBucketsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[logging_config.LogBucket]:
        for page in self.pages:
            yield from page.buckets

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListBucketsAsyncPager:
    """A pager for iterating through ``list_buckets`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListBucketsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``buckets`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListBuckets`` requests and continue to iterate
    through the ``buckets`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListBucketsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[logging_config.ListBucketsResponse]],
            request: logging_config.ListBucketsRequest,
            response: logging_config.ListBucketsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListBucketsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListBucketsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListBucketsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[logging_config.ListBucketsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[logging_config.LogBucket]:
        async def async_generator():
            async for page in self.pages:
                for response in page.buckets:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListViewsPager:
    """A pager for iterating through ``list_views`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListViewsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``views`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListViews`` requests and continue to iterate
    through the ``views`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListViewsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., logging_config.ListViewsResponse],
            request: logging_config.ListViewsRequest,
            response: logging_config.ListViewsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListViewsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListViewsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListViewsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[logging_config.ListViewsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[logging_config.LogView]:
        for page in self.pages:
            yield from page.views

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListViewsAsyncPager:
    """A pager for iterating through ``list_views`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListViewsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``views`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListViews`` requests and continue to iterate
    through the ``views`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListViewsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[logging_config.ListViewsResponse]],
            request: logging_config.ListViewsRequest,
            response: logging_config.ListViewsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListViewsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListViewsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListViewsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[logging_config.ListViewsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[logging_config.LogView]:
        async def async_generator():
            async for page in self.pages:
                for response in page.views:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListExclusionsPager:
    """A pager for iterating through ``list_exclusions`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListExclusionsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``exclusions`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListExclusions`` requests and continue to iterate
    through the ``exclusions`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListExclusionsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., logging_config.ListExclusionsResponse],
            request: logging_config.ListExclusionsRequest,
            response: logging_config.ListExclusionsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListExclusionsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListExclusionsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListExclusionsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[logging_config.ListExclusionsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[logging_config.LogExclusion]:
        for page in self.pages:
            yield from page.exclusions

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListExclusionsAsyncPager:
    """A pager for iterating through ``list_exclusions`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListExclusionsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``exclusions`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListExclusions`` requests and continue to iterate
    through the ``exclusions`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListExclusionsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[logging_config.ListExclusionsResponse]],
            request: logging_config.ListExclusionsRequest,
            response: logging_config.ListExclusionsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListExclusionsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListExclusionsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListExclusionsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[logging_config.ListExclusionsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[logging_config.LogExclusion]:
        async def async_generator():
            async for page in self.pages:
                for response in page.exclusions:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListSinksPager:
    """A pager for iterating through ``list_sinks`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSinksResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``sinks`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListSinks`` requests and continue to iterate
    through the ``sinks`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSinksResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., logging_config.ListSinksResponse],
            request: logging_config.ListSinksRequest,
            response: logging_config.ListSinksResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSinksRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSinksResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListSinksRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[logging_config.ListSinksResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[logging_config.LogSink]:
        for page in self.pages:
            yield from page.sinks

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListSinksAsyncPager:
    """A pager for iterating through ``list_sinks`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSinksResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``sinks`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListSinks`` requests and continue to iterate
    through the ``sinks`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSinksResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[logging_config.ListSinksResponse]],
            request: logging_config.ListSinksRequest,
            response: logging_config.ListSinksResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSinksRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSinksResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListSinksRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[logging_config.ListSinksResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[logging_config.LogSink]:
        async def async_generator():
            async for page in self.pages:
                for response in page.sinks:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListLinksPager:
    """A pager for iterating through ``list_links`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLinksResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``links`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListLinks`` requests and continue to iterate
    through the ``links`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLinksResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., logging_config.ListLinksResponse],
            request: logging_config.ListLinksRequest,
            response: logging_config.ListLinksResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLinksRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLinksResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListLinksRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[logging_config.ListLinksResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[logging_config.Link]:
        for page in self.pages:
            yield from page.links

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListLinksAsyncPager:
    """A pager for iterating through ``list_links`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLinksResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``links`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListLinks`` requests and continue to iterate
    through the ``links`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLinksResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[logging_config.ListLinksResponse]],
            request: logging_config.ListLinksRequest,
            response: logging_config.ListLinksResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLinksRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLinksResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListLinksRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[logging_config.ListLinksResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[logging_config.Link]:
        async def async_generator():
            async for page in self.pages:
                for response in page.links:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListSavedQueriesPager:
    """A pager for iterating through ``list_saved_queries`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSavedQueriesResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``saved_queries`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListSavedQueries`` requests and continue to iterate
    through the ``saved_queries`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSavedQueriesResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., logging_config.ListSavedQueriesResponse],
            request: logging_config.ListSavedQueriesRequest,
            response: logging_config.ListSavedQueriesResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSavedQueriesRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSavedQueriesResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListSavedQueriesRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[logging_config.ListSavedQueriesResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[logging_config.SavedQuery]:
        for page in self.pages:
            yield from page.saved_queries

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListSavedQueriesAsyncPager:
    """A pager for iterating through ``list_saved_queries`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSavedQueriesResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``saved_queries`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListSavedQueries`` requests and continue to iterate
    through the ``saved_queries`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSavedQueriesResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[logging_config.ListSavedQueriesResponse]],
            request: logging_config.ListSavedQueriesRequest,
            response: logging_config.ListSavedQueriesResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSavedQueriesRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSavedQueriesResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListSavedQueriesRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[logging_config.ListSavedQueriesResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[logging_config.SavedQuery]:
        async def async_generator():
            async for page in self.pages:
                for response in page.saved_queries:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListRecentQueriesPager:
    """A pager for iterating through ``list_recent_queries`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListRecentQueriesResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``recent_queries`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListRecentQueries`` requests and continue to iterate
    through the ``recent_queries`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListRecentQueriesResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., logging_config.ListRecentQueriesResponse],
            request: logging_config.ListRecentQueriesRequest,
            response: logging_config.ListRecentQueriesResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListRecentQueriesRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListRecentQueriesResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListRecentQueriesRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[logging_config.ListRecentQueriesResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[logging_config.RecentQuery]:
        for page in self.pages:
            yield from page.recent_queries

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListRecentQueriesAsyncPager:
    """A pager for iterating through ``list_recent_queries`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListRecentQueriesResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``recent_queries`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListRecentQueries`` requests and continue to iterate
    through the ``recent_queries`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListRecentQueriesResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[logging_config.ListRecentQueriesResponse]],
            request: logging_config.ListRecentQueriesRequest,
            response: logging_config.ListRecentQueriesResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListRecentQueriesRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListRecentQueriesResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = logging_config.ListRecentQueriesRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[logging_config.ListRecentQueriesResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[logging_config.RecentQuery]:
        async def async_generator():
            async for page in self.pages:
                for response in page.recent_queries:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)
