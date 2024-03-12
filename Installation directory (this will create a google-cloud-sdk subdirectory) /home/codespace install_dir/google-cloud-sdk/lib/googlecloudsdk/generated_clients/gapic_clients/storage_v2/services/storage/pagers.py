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

from googlecloudsdk.generated_clients.gapic_clients.storage_v2.types import storage


class ListBucketsPager:
    """A pager for iterating through ``list_buckets`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListBucketsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``buckets`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListBuckets`` requests and continue to iterate
    through the ``buckets`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListBucketsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., storage.ListBucketsResponse],
            request: storage.ListBucketsRequest,
            response: storage.ListBucketsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListBucketsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListBucketsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = storage.ListBucketsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[storage.ListBucketsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[storage.Bucket]:
        for page in self.pages:
            yield from page.buckets

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListBucketsAsyncPager:
    """A pager for iterating through ``list_buckets`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListBucketsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``buckets`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListBuckets`` requests and continue to iterate
    through the ``buckets`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListBucketsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[storage.ListBucketsResponse]],
            request: storage.ListBucketsRequest,
            response: storage.ListBucketsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListBucketsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListBucketsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = storage.ListBucketsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[storage.ListBucketsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[storage.Bucket]:
        async def async_generator():
            async for page in self.pages:
                for response in page.buckets:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListObjectsPager:
    """A pager for iterating through ``list_objects`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListObjectsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``objects`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListObjects`` requests and continue to iterate
    through the ``objects`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListObjectsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., storage.ListObjectsResponse],
            request: storage.ListObjectsRequest,
            response: storage.ListObjectsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListObjectsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListObjectsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = storage.ListObjectsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[storage.ListObjectsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[storage.Object]:
        for page in self.pages:
            yield from page.objects

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListObjectsAsyncPager:
    """A pager for iterating through ``list_objects`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListObjectsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``objects`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListObjects`` requests and continue to iterate
    through the ``objects`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListObjectsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[storage.ListObjectsResponse]],
            request: storage.ListObjectsRequest,
            response: storage.ListObjectsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListObjectsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListObjectsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = storage.ListObjectsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[storage.ListObjectsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[storage.Object]:
        async def async_generator():
            async for page in self.pages:
                for response in page.objects:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListHmacKeysPager:
    """A pager for iterating through ``list_hmac_keys`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListHmacKeysResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``hmac_keys`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListHmacKeys`` requests and continue to iterate
    through the ``hmac_keys`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListHmacKeysResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., storage.ListHmacKeysResponse],
            request: storage.ListHmacKeysRequest,
            response: storage.ListHmacKeysResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListHmacKeysRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListHmacKeysResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = storage.ListHmacKeysRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[storage.ListHmacKeysResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[storage.HmacKeyMetadata]:
        for page in self.pages:
            yield from page.hmac_keys

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListHmacKeysAsyncPager:
    """A pager for iterating through ``list_hmac_keys`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListHmacKeysResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``hmac_keys`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListHmacKeys`` requests and continue to iterate
    through the ``hmac_keys`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListHmacKeysResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[storage.ListHmacKeysResponse]],
            request: storage.ListHmacKeysRequest,
            response: storage.ListHmacKeysResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListHmacKeysRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListHmacKeysResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = storage.ListHmacKeysRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[storage.ListHmacKeysResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[storage.HmacKeyMetadata]:
        async def async_generator():
            async for page in self.pages:
                for response in page.hmac_keys:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListNotificationConfigsPager:
    """A pager for iterating through ``list_notification_configs`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListNotificationConfigsResponse` object, and
    provides an ``__iter__`` method to iterate through its
    ``notification_configs`` field.

    If there are more pages, the ``__iter__`` method will make additional
    ``ListNotificationConfigs`` requests and continue to iterate
    through the ``notification_configs`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListNotificationConfigsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., storage.ListNotificationConfigsResponse],
            request: storage.ListNotificationConfigsRequest,
            response: storage.ListNotificationConfigsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiate the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListNotificationConfigsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListNotificationConfigsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = storage.ListNotificationConfigsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def pages(self) -> Iterator[storage.ListNotificationConfigsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = self._method(self._request, metadata=self._metadata)
            yield self._response

    def __iter__(self) -> Iterator[storage.NotificationConfig]:
        for page in self.pages:
            yield from page.notification_configs

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)


class ListNotificationConfigsAsyncPager:
    """A pager for iterating through ``list_notification_configs`` requests.

    This class thinly wraps an initial
    :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListNotificationConfigsResponse` object, and
    provides an ``__aiter__`` method to iterate through its
    ``notification_configs`` field.

    If there are more pages, the ``__aiter__`` method will make additional
    ``ListNotificationConfigs`` requests and continue to iterate
    through the ``notification_configs`` field on the
    corresponding responses.

    All the usual :class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListNotificationConfigsResponse`
    attributes are available on the pager. If multiple requests are made, only
    the most recent response is retained, and thus used for attribute lookup.
    """
    def __init__(self,
            method: Callable[..., Awaitable[storage.ListNotificationConfigsResponse]],
            request: storage.ListNotificationConfigsRequest,
            response: storage.ListNotificationConfigsResponse,
            *,
            metadata: Sequence[Tuple[str, str]] = ()):
        """Instantiates the pager.

        Args:
            method (Callable): The method that was originally called, and
                which instantiated this pager.
            request (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListNotificationConfigsRequest):
                The initial request object.
            response (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListNotificationConfigsResponse):
                The initial response object.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        self._method = method
        self._request = storage.ListNotificationConfigsRequest(request)
        self._response = response
        self._metadata = metadata

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    async def pages(self) -> AsyncIterator[storage.ListNotificationConfigsResponse]:
        yield self._response
        while self._response.next_page_token:
            self._request.page_token = self._response.next_page_token
            self._response = await self._method(self._request, metadata=self._metadata)
            yield self._response
    def __aiter__(self) -> AsyncIterator[storage.NotificationConfig]:
        async def async_generator():
            async for page in self.pages:
                for response in page.notification_configs:
                    yield response

        return async_generator()

    def __repr__(self) -> str:
        return '{0}<{1!r}>'.format(self.__class__.__name__, self._response)
