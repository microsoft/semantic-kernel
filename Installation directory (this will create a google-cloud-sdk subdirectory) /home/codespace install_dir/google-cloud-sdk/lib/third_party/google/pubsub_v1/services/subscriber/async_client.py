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
from collections import OrderedDict
import functools
import re
from typing import (
    Dict,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    AsyncIterable,
    Awaitable,
    AsyncIterator,
    Sequence,
    Tuple,
    Type,
    Union,
)

import warnings
from google.pubsub_v1 import gapic_version as package_version

from google.api_core.client_options import ClientOptions
from google.api_core import exceptions as core_exceptions
from google.api_core import gapic_v1
from google.api_core import retry as retries
from google.auth import credentials as ga_credentials  # type: ignore
from google.oauth2 import service_account  # type: ignore

try:
    OptionalRetry = Union[retries.Retry, gapic_v1.method._MethodDefault]
except AttributeError:  # pragma: NO COVER
    OptionalRetry = Union[retries.Retry, object]  # type: ignore

from google.iam.v1 import iam_policy_pb2  # type: ignore
from google.iam.v1 import policy_pb2  # type: ignore
from cloudsdk.google.protobuf import duration_pb2  # type: ignore
from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore
from google.pubsub_v1.services.subscriber import pagers
from google.pubsub_v1.types import pubsub
from .transports.base import SubscriberTransport, DEFAULT_CLIENT_INFO
from .transports.grpc_asyncio import SubscriberGrpcAsyncIOTransport
from .client import SubscriberClient


class SubscriberAsyncClient:
    """The service that an application uses to manipulate subscriptions and
    to consume messages from a subscription via the ``Pull`` method or
    by establishing a bi-directional stream using the ``StreamingPull``
    method.
    """

    _client: SubscriberClient

    DEFAULT_ENDPOINT = SubscriberClient.DEFAULT_ENDPOINT
    DEFAULT_MTLS_ENDPOINT = SubscriberClient.DEFAULT_MTLS_ENDPOINT

    snapshot_path = staticmethod(SubscriberClient.snapshot_path)
    parse_snapshot_path = staticmethod(SubscriberClient.parse_snapshot_path)
    subscription_path = staticmethod(SubscriberClient.subscription_path)
    parse_subscription_path = staticmethod(SubscriberClient.parse_subscription_path)
    topic_path = staticmethod(SubscriberClient.topic_path)
    parse_topic_path = staticmethod(SubscriberClient.parse_topic_path)
    common_billing_account_path = staticmethod(
        SubscriberClient.common_billing_account_path
    )
    parse_common_billing_account_path = staticmethod(
        SubscriberClient.parse_common_billing_account_path
    )
    common_folder_path = staticmethod(SubscriberClient.common_folder_path)
    parse_common_folder_path = staticmethod(SubscriberClient.parse_common_folder_path)
    common_organization_path = staticmethod(SubscriberClient.common_organization_path)
    parse_common_organization_path = staticmethod(
        SubscriberClient.parse_common_organization_path
    )
    common_project_path = staticmethod(SubscriberClient.common_project_path)
    parse_common_project_path = staticmethod(SubscriberClient.parse_common_project_path)
    common_location_path = staticmethod(SubscriberClient.common_location_path)
    parse_common_location_path = staticmethod(
        SubscriberClient.parse_common_location_path
    )

    @classmethod
    def from_service_account_info(cls, info: dict, *args, **kwargs):
        """Creates an instance of this client using the provided credentials
            info.

        Args:
            info (dict): The service account private key info.
            args: Additional arguments to pass to the constructor.
            kwargs: Additional arguments to pass to the constructor.

        Returns:
            SubscriberAsyncClient: The constructed client.
        """
        return SubscriberClient.from_service_account_info.__func__(SubscriberAsyncClient, info, *args, **kwargs)  # type: ignore

    @classmethod
    def from_service_account_file(cls, filename: str, *args, **kwargs):
        """Creates an instance of this client using the provided credentials
            file.

        Args:
            filename (str): The path to the service account private key json
                file.
            args: Additional arguments to pass to the constructor.
            kwargs: Additional arguments to pass to the constructor.

        Returns:
            SubscriberAsyncClient: The constructed client.
        """
        return SubscriberClient.from_service_account_file.__func__(SubscriberAsyncClient, filename, *args, **kwargs)  # type: ignore

    from_service_account_json = from_service_account_file

    @classmethod
    def get_mtls_endpoint_and_cert_source(
        cls, client_options: Optional[ClientOptions] = None
    ):
        """Return the API endpoint and client cert source for mutual TLS.

        The client cert source is determined in the following order:
        (1) if `GOOGLE_API_USE_CLIENT_CERTIFICATE` environment variable is not "true", the
        client cert source is None.
        (2) if `client_options.client_cert_source` is provided, use the provided one; if the
        default client cert source exists, use the default one; otherwise the client cert
        source is None.

        The API endpoint is determined in the following order:
        (1) if `client_options.api_endpoint` if provided, use the provided one.
        (2) if `GOOGLE_API_USE_CLIENT_CERTIFICATE` environment variable is "always", use the
        default mTLS endpoint; if the environment variable is "never", use the default API
        endpoint; otherwise if client cert source exists, use the default mTLS endpoint, otherwise
        use the default API endpoint.

        More details can be found at https://google.aip.dev/auth/4114.

        Args:
            client_options (google.api_core.client_options.ClientOptions): Custom options for the
                client. Only the `api_endpoint` and `client_cert_source` properties may be used
                in this method.

        Returns:
            Tuple[str, Callable[[], Tuple[bytes, bytes]]]: returns the API endpoint and the
                client cert source to use.

        Raises:
            google.auth.exceptions.MutualTLSChannelError: If any errors happen.
        """
        return SubscriberClient.get_mtls_endpoint_and_cert_source(client_options)  # type: ignore

    @property
    def transport(self) -> SubscriberTransport:
        """Returns the transport used by the client instance.

        Returns:
            SubscriberTransport: The transport used by the client instance.
        """
        return self._client.transport

    get_transport_class = functools.partial(
        type(SubscriberClient).get_transport_class, type(SubscriberClient)
    )

    def __init__(
        self,
        *,
        credentials: Optional[ga_credentials.Credentials] = None,
        transport: Union[str, SubscriberTransport] = "grpc_asyncio",
        client_options: Optional[ClientOptions] = None,
        client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
    ) -> None:
        """Instantiates the subscriber client.

        Args:
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
            transport (Union[str, ~.SubscriberTransport]): The
                transport to use. If set to None, a transport is chosen
                automatically.
            client_options (ClientOptions): Custom options for the client. It
                won't take effect if a ``transport`` instance is provided.
                (1) The ``api_endpoint`` property can be used to override the
                default endpoint provided by the client. GOOGLE_API_USE_MTLS_ENDPOINT
                environment variable can also be used to override the endpoint:
                "always" (always use the default mTLS endpoint), "never" (always
                use the default regular endpoint) and "auto" (auto switch to the
                default mTLS endpoint if client certificate is present, this is
                the default value). However, the ``api_endpoint`` property takes
                precedence if provided.
                (2) If GOOGLE_API_USE_CLIENT_CERTIFICATE environment variable
                is "true", then the ``client_cert_source`` property can be used
                to provide client certificate for mutual TLS transport. If
                not provided, the default SSL client certificate will be used if
                present. If GOOGLE_API_USE_CLIENT_CERTIFICATE is "false" or not
                set, no client certificate will be used.

        Raises:
            google.auth.exceptions.MutualTlsChannelError: If mutual TLS transport
                creation failed for any reason.
        """
        self._client = SubscriberClient(
            credentials=credentials,
            transport=transport,
            client_options=client_options,
            client_info=client_info,
        )

    async def create_subscription(
        self,
        request: Optional[Union[pubsub.Subscription, dict]] = None,
        *,
        name: Optional[str] = None,
        topic: Optional[str] = None,
        push_config: Optional[pubsub.PushConfig] = None,
        ack_deadline_seconds: Optional[int] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pubsub.Subscription:
        r"""Creates a subscription to a given topic. See the [resource name
        rules]
        (https://cloud.google.com/pubsub/docs/admin#resource_names). If
        the subscription already exists, returns ``ALREADY_EXISTS``. If
        the corresponding topic doesn't exist, returns ``NOT_FOUND``.

        If the name is not provided in the request, the server will
        assign a random name for this subscription on the same project
        as the topic, conforming to the [resource name format]
        (https://cloud.google.com/pubsub/docs/admin#resource_names). The
        generated name is populated in the returned Subscription object.
        Note that for REST API requests, you must specify a name in the
        request.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_create_subscription():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.Subscription(
                    name="name_value",
                    topic="topic_value",
                )

                # Make the request
                response = await client.create_subscription(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.pubsub_v1.types.Subscription, dict]]):
                The request object. A subscription resource. If none of ``push_config``,
                ``bigquery_config``, or ``cloud_storage_config`` is set,
                then the subscriber will pull and ack messages using API
                methods. At most one of these fields may be set.
            name (:class:`str`):
                Required. The name of the subscription. It must have the
                format
                ``"projects/{project}/subscriptions/{subscription}"``.
                ``{subscription}`` must start with a letter, and contain
                only letters (``[A-Za-z]``), numbers (``[0-9]``), dashes
                (``-``), underscores (``_``), periods (``.``), tildes
                (``~``), plus (``+``) or percent signs (``%``). It must
                be between 3 and 255 characters in length, and it must
                not start with ``"goog"``.

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            topic (:class:`str`):
                Required. The name of the topic from which this
                subscription is receiving messages. Format is
                ``projects/{project}/topics/{topic}``. The value of this
                field will be ``_deleted-topic_`` if the topic has been
                deleted.

                This corresponds to the ``topic`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            push_config (:class:`google.pubsub_v1.types.PushConfig`):
                If push delivery is used with this
                subscription, this field is used to
                configure it.

                This corresponds to the ``push_config`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            ack_deadline_seconds (:class:`int`):
                The approximate amount of time (on a best-effort basis)
                Pub/Sub waits for the subscriber to acknowledge receipt
                before resending the message. In the interval after the
                message is delivered and before it is acknowledged, it
                is considered to be *outstanding*. During that time
                period, the message will not be redelivered (on a
                best-effort basis).

                For pull subscriptions, this value is used as the
                initial value for the ack deadline. To override this
                value for a given message, call ``ModifyAckDeadline``
                with the corresponding ``ack_id`` if using non-streaming
                pull or send the ``ack_id`` in a
                ``StreamingModifyAckDeadlineRequest`` if using streaming
                pull. The minimum custom deadline you can specify is 10
                seconds. The maximum custom deadline you can specify is
                600 seconds (10 minutes). If this parameter is 0, a
                default value of 10 seconds is used.

                For push delivery, this value is also used to set the
                request timeout for the call to the push endpoint.

                If the subscriber never acknowledges the message, the
                Pub/Sub system will eventually redeliver the message.

                This corresponds to the ``ack_deadline_seconds`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.pubsub_v1.types.Subscription:
                A subscription resource. If none of push_config, bigquery_config, or
                   cloud_storage_config is set, then the subscriber will
                   pull and ack messages using API methods. At most one
                   of these fields may be set.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name, topic, push_config, ack_deadline_seconds])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.Subscription(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name
        if topic is not None:
            request.topic = topic
        if push_config is not None:
            request.push_config = push_config
        if ack_deadline_seconds is not None:
            request.ack_deadline_seconds = ack_deadline_seconds

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_subscription,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.Aborted,
                    core_exceptions.ServiceUnavailable,
                    core_exceptions.Unknown,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("name", request.name),)),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def get_subscription(
        self,
        request: Optional[Union[pubsub.GetSubscriptionRequest, dict]] = None,
        *,
        subscription: Optional[str] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pubsub.Subscription:
        r"""Gets the configuration details of a subscription.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_get_subscription():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.GetSubscriptionRequest(
                    subscription="subscription_value",
                )

                # Make the request
                response = await client.get_subscription(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.pubsub_v1.types.GetSubscriptionRequest, dict]]):
                The request object. Request for the GetSubscription
                method.
            subscription (:class:`str`):
                Required. The name of the subscription to get. Format is
                ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.pubsub_v1.types.Subscription:
                A subscription resource. If none of push_config, bigquery_config, or
                   cloud_storage_config is set, then the subscriber will
                   pull and ack messages using API methods. At most one
                   of these fields may be set.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([subscription])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.GetSubscriptionRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if subscription is not None:
            request.subscription = subscription

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_subscription,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.Aborted,
                    core_exceptions.ServiceUnavailable,
                    core_exceptions.Unknown,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def update_subscription(
        self,
        request: Optional[Union[pubsub.UpdateSubscriptionRequest, dict]] = None,
        *,
        subscription: Optional[pubsub.Subscription] = None,
        update_mask: Optional[field_mask_pb2.FieldMask] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pubsub.Subscription:
        r"""Updates an existing subscription. Note that certain
        properties of a subscription, such as its topic, are not
        modifiable.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_update_subscription():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                subscription = pubsub_v1.Subscription()
                subscription.name = "name_value"
                subscription.topic = "topic_value"

                request = pubsub_v1.UpdateSubscriptionRequest(
                    subscription=subscription,
                )

                # Make the request
                response = await client.update_subscription(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.pubsub_v1.types.UpdateSubscriptionRequest, dict]]):
                The request object. Request for the UpdateSubscription
                method.
            subscription (:class:`google.pubsub_v1.types.Subscription`):
                Required. The updated subscription
                object.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
                Required. Indicates which fields in
                the provided subscription to update.
                Must be specified and non-empty.

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.pubsub_v1.types.Subscription:
                A subscription resource. If none of push_config, bigquery_config, or
                   cloud_storage_config is set, then the subscriber will
                   pull and ack messages using API methods. At most one
                   of these fields may be set.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([subscription, update_mask])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.UpdateSubscriptionRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if subscription is not None:
            request.subscription = subscription
        if update_mask is not None:
            request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_subscription,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.ServiceUnavailable,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription.name", request.subscription.name),)
            ),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def list_subscriptions(
        self,
        request: Optional[Union[pubsub.ListSubscriptionsRequest, dict]] = None,
        *,
        project: Optional[str] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pagers.ListSubscriptionsAsyncPager:
        r"""Lists matching subscriptions.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_list_subscriptions():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.ListSubscriptionsRequest(
                    project="project_value",
                )

                # Make the request
                page_result = client.list_subscriptions(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[google.pubsub_v1.types.ListSubscriptionsRequest, dict]]):
                The request object. Request for the ``ListSubscriptions`` method.
            project (:class:`str`):
                Required. The name of the project in which to list
                subscriptions. Format is ``projects/{project-id}``.

                This corresponds to the ``project`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.pubsub_v1.services.subscriber.pagers.ListSubscriptionsAsyncPager:
                Response for the ListSubscriptions method.

                Iterating over this object will yield results and
                resolve additional pages automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([project])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.ListSubscriptionsRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if project is not None:
            request.project = project

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_subscriptions,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.Aborted,
                    core_exceptions.ServiceUnavailable,
                    core_exceptions.Unknown,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("project", request.project),)),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # This method is paged; wrap the response in a pager, which provides
        # an `__aiter__` convenience method.
        response = pagers.ListSubscriptionsAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def delete_subscription(
        self,
        request: Optional[Union[pubsub.DeleteSubscriptionRequest, dict]] = None,
        *,
        subscription: Optional[str] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> None:
        r"""Deletes an existing subscription. All messages retained in the
        subscription are immediately dropped. Calls to ``Pull`` after
        deletion will return ``NOT_FOUND``. After a subscription is
        deleted, a new one may be created with the same name, but the
        new one has no association with the old subscription or its
        topic unless the same topic is specified.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_delete_subscription():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.DeleteSubscriptionRequest(
                    subscription="subscription_value",
                )

                # Make the request
                await client.delete_subscription(request=request)

        Args:
            request (Optional[Union[google.pubsub_v1.types.DeleteSubscriptionRequest, dict]]):
                The request object. Request for the DeleteSubscription
                method.
            subscription (:class:`str`):
                Required. The subscription to delete. Format is
                ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([subscription])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.DeleteSubscriptionRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if subscription is not None:
            request.subscription = subscription

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_subscription,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.ServiceUnavailable,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def modify_ack_deadline(
        self,
        request: Optional[Union[pubsub.ModifyAckDeadlineRequest, dict]] = None,
        *,
        subscription: Optional[str] = None,
        ack_ids: Optional[MutableSequence[str]] = None,
        ack_deadline_seconds: Optional[int] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> None:
        r"""Modifies the ack deadline for a specific message. This method is
        useful to indicate that more time is needed to process a message
        by the subscriber, or to make the message available for
        redelivery if the processing was interrupted. Note that this
        does not modify the subscription-level ``ackDeadlineSeconds``
        used for subsequent messages.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_modify_ack_deadline():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.ModifyAckDeadlineRequest(
                    subscription="subscription_value",
                    ack_ids=['ack_ids_value1', 'ack_ids_value2'],
                    ack_deadline_seconds=2066,
                )

                # Make the request
                await client.modify_ack_deadline(request=request)

        Args:
            request (Optional[Union[google.pubsub_v1.types.ModifyAckDeadlineRequest, dict]]):
                The request object. Request for the ModifyAckDeadline
                method.
            subscription (:class:`str`):
                Required. The name of the subscription. Format is
                ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            ack_ids (:class:`MutableSequence[str]`):
                Required. List of acknowledgment IDs.
                This corresponds to the ``ack_ids`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            ack_deadline_seconds (:class:`int`):
                Required. The new ack deadline with respect to the time
                this request was sent to the Pub/Sub system. For
                example, if the value is 10, the new ack deadline will
                expire 10 seconds after the ``ModifyAckDeadline`` call
                was made. Specifying zero might immediately make the
                message available for delivery to another subscriber
                client. This typically results in an increase in the
                rate of message redeliveries (that is, duplicates). The
                minimum deadline you can specify is 0 seconds. The
                maximum deadline you can specify is 600 seconds (10
                minutes).

                This corresponds to the ``ack_deadline_seconds`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([subscription, ack_ids, ack_deadline_seconds])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.ModifyAckDeadlineRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if subscription is not None:
            request.subscription = subscription
        if ack_deadline_seconds is not None:
            request.ack_deadline_seconds = ack_deadline_seconds
        if ack_ids:
            request.ack_ids.extend(ack_ids)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.modify_ack_deadline,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.ServiceUnavailable,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def acknowledge(
        self,
        request: Optional[Union[pubsub.AcknowledgeRequest, dict]] = None,
        *,
        subscription: Optional[str] = None,
        ack_ids: Optional[MutableSequence[str]] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> None:
        r"""Acknowledges the messages associated with the ``ack_ids`` in the
        ``AcknowledgeRequest``. The Pub/Sub system can remove the
        relevant messages from the subscription.

        Acknowledging a message whose ack deadline has expired may
        succeed, but such a message may be redelivered later.
        Acknowledging a message more than once will not result in an
        error.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_acknowledge():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.AcknowledgeRequest(
                    subscription="subscription_value",
                    ack_ids=['ack_ids_value1', 'ack_ids_value2'],
                )

                # Make the request
                await client.acknowledge(request=request)

        Args:
            request (Optional[Union[google.pubsub_v1.types.AcknowledgeRequest, dict]]):
                The request object. Request for the Acknowledge method.
            subscription (:class:`str`):
                Required. The subscription whose message is being
                acknowledged. Format is
                ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            ack_ids (:class:`MutableSequence[str]`):
                Required. The acknowledgment ID for the messages being
                acknowledged that was returned by the Pub/Sub system in
                the ``Pull`` response. Must not be empty.

                This corresponds to the ``ack_ids`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([subscription, ack_ids])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.AcknowledgeRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if subscription is not None:
            request.subscription = subscription
        if ack_ids:
            request.ack_ids.extend(ack_ids)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.acknowledge,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.ServiceUnavailable,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def pull(
        self,
        request: Optional[Union[pubsub.PullRequest, dict]] = None,
        *,
        subscription: Optional[str] = None,
        return_immediately: Optional[bool] = None,
        max_messages: Optional[int] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pubsub.PullResponse:
        r"""Pulls messages from the server.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_pull():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.PullRequest(
                    subscription="subscription_value",
                    max_messages=1277,
                )

                # Make the request
                response = await client.pull(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.pubsub_v1.types.PullRequest, dict]]):
                The request object. Request for the ``Pull`` method.
            subscription (:class:`str`):
                Required. The subscription from which messages should be
                pulled. Format is
                ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            return_immediately (:class:`bool`):
                Optional. If this field set to true, the system will
                respond immediately even if it there are no messages
                available to return in the ``Pull`` response. Otherwise,
                the system may wait (for a bounded amount of time) until
                at least one message is available, rather than returning
                no messages. Warning: setting this field to ``true`` is
                discouraged because it adversely impacts the performance
                of ``Pull`` operations. We recommend that users do not
                set this field.

                This corresponds to the ``return_immediately`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            max_messages (:class:`int`):
                Required. The maximum number of
                messages to return for this request.
                Must be a positive integer. The Pub/Sub
                system may return fewer than the number
                specified.

                This corresponds to the ``max_messages`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.pubsub_v1.types.PullResponse:
                Response for the Pull method.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([subscription, return_immediately, max_messages])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.PullRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if subscription is not None:
            request.subscription = subscription
        if return_immediately is not None:
            request.return_immediately = return_immediately
        if max_messages is not None:
            request.max_messages = max_messages

        if request.return_immediately:
            warnings.warn(
                "The return_immediately flag is deprecated and should be set to False.",
                category=DeprecationWarning,
            )

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.pull,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.Aborted,
                    core_exceptions.InternalServerError,
                    core_exceptions.ServiceUnavailable,
                    core_exceptions.Unknown,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def streaming_pull(
        self,
        requests: Optional[AsyncIterator[pubsub.StreamingPullRequest]] = None,
        *,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> Awaitable[AsyncIterable[pubsub.StreamingPullResponse]]:
        r"""Establishes a stream with the server, which sends messages down
        to the client. The client streams acknowledgements and ack
        deadline modifications back to the server. The server will close
        the stream and return the status on any error. The server may
        close the stream with status ``UNAVAILABLE`` to reassign
        server-side resources, in which case, the client should
        re-establish the stream. Flow control can be achieved by
        configuring the underlying RPC channel.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_streaming_pull():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.StreamingPullRequest(
                    subscription="subscription_value",
                    stream_ack_deadline_seconds=2813,
                )

                # This method expects an iterator which contains
                # 'pubsub_v1.StreamingPullRequest' objects
                # Here we create a generator that yields a single `request` for
                # demonstrative purposes.
                requests = [request]

                def request_generator():
                    for request in requests:
                        yield request

                # Make the request
                stream = await client.streaming_pull(requests=request_generator())

                # Handle the response
                async for response in stream:
                    print(response)

        Args:
            requests (AsyncIterator[`google.pubsub_v1.types.StreamingPullRequest`]):
                The request object AsyncIterator. Request for the ``StreamingPull`` streaming RPC method.
                This request is used to establish the initial stream as
                well as to stream acknowledgements and ack deadline
                modifications from the client to the server.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            AsyncIterable[google.pubsub_v1.types.StreamingPullResponse]:
                Response for the StreamingPull method. This response is used to stream
                   messages from the server to the client.

        """

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.streaming_pull,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=4.0,
                predicate=retries.if_exception_type(
                    core_exceptions.Aborted,
                    core_exceptions.DeadlineExceeded,
                    core_exceptions.InternalServerError,
                    core_exceptions.ResourceExhausted,
                    core_exceptions.ServiceUnavailable,
                ),
                deadline=900.0,
            ),
            default_timeout=900.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Send the request.
        response = rpc(
            requests,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def modify_push_config(
        self,
        request: Optional[Union[pubsub.ModifyPushConfigRequest, dict]] = None,
        *,
        subscription: Optional[str] = None,
        push_config: Optional[pubsub.PushConfig] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> None:
        r"""Modifies the ``PushConfig`` for a specified subscription.

        This may be used to change a push subscription to a pull one
        (signified by an empty ``PushConfig``) or vice versa, or change
        the endpoint URL and other attributes of a push subscription.
        Messages will accumulate for delivery continuously through the
        call regardless of changes to the ``PushConfig``.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_modify_push_config():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.ModifyPushConfigRequest(
                    subscription="subscription_value",
                )

                # Make the request
                await client.modify_push_config(request=request)

        Args:
            request (Optional[Union[google.pubsub_v1.types.ModifyPushConfigRequest, dict]]):
                The request object. Request for the ModifyPushConfig
                method.
            subscription (:class:`str`):
                Required. The name of the subscription. Format is
                ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            push_config (:class:`google.pubsub_v1.types.PushConfig`):
                Required. The push configuration for future deliveries.

                An empty ``pushConfig`` indicates that the Pub/Sub
                system should stop pushing messages from the given
                subscription and allow messages to be pulled and
                acknowledged - effectively pausing the subscription if
                ``Pull`` or ``StreamingPull`` is not called.

                This corresponds to the ``push_config`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([subscription, push_config])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.ModifyPushConfigRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if subscription is not None:
            request.subscription = subscription
        if push_config is not None:
            request.push_config = push_config

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.modify_push_config,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.ServiceUnavailable,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def get_snapshot(
        self,
        request: Optional[Union[pubsub.GetSnapshotRequest, dict]] = None,
        *,
        snapshot: Optional[str] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pubsub.Snapshot:
        r"""Gets the configuration details of a snapshot. Snapshots are used
        in
        `Seek <https://cloud.google.com/pubsub/docs/replay-overview>`__
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_get_snapshot():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.GetSnapshotRequest(
                    snapshot="snapshot_value",
                )

                # Make the request
                response = await client.get_snapshot(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.pubsub_v1.types.GetSnapshotRequest, dict]]):
                The request object. Request for the GetSnapshot method.
            snapshot (:class:`str`):
                Required. The name of the snapshot to get. Format is
                ``projects/{project}/snapshots/{snap}``.

                This corresponds to the ``snapshot`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.pubsub_v1.types.Snapshot:
                A snapshot resource. Snapshots are used in
                   [Seek](https://cloud.google.com/pubsub/docs/replay-overview)
                   operations, which allow you to manage message
                   acknowledgments in bulk. That is, you can set the
                   acknowledgment state of messages in an existing
                   subscription to the state captured by a snapshot.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([snapshot])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.GetSnapshotRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if snapshot is not None:
            request.snapshot = snapshot

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_snapshot,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.Aborted,
                    core_exceptions.ServiceUnavailable,
                    core_exceptions.Unknown,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("snapshot", request.snapshot),)),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def list_snapshots(
        self,
        request: Optional[Union[pubsub.ListSnapshotsRequest, dict]] = None,
        *,
        project: Optional[str] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pagers.ListSnapshotsAsyncPager:
        r"""Lists the existing snapshots. Snapshots are used in
        `Seek <https://cloud.google.com/pubsub/docs/replay-overview>`__
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_list_snapshots():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.ListSnapshotsRequest(
                    project="project_value",
                )

                # Make the request
                page_result = client.list_snapshots(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[google.pubsub_v1.types.ListSnapshotsRequest, dict]]):
                The request object. Request for the ``ListSnapshots`` method.
            project (:class:`str`):
                Required. The name of the project in which to list
                snapshots. Format is ``projects/{project-id}``.

                This corresponds to the ``project`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.pubsub_v1.services.subscriber.pagers.ListSnapshotsAsyncPager:
                Response for the ListSnapshots method.

                Iterating over this object will yield results and
                resolve additional pages automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([project])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.ListSnapshotsRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if project is not None:
            request.project = project

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_snapshots,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.Aborted,
                    core_exceptions.ServiceUnavailable,
                    core_exceptions.Unknown,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("project", request.project),)),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # This method is paged; wrap the response in a pager, which provides
        # an `__aiter__` convenience method.
        response = pagers.ListSnapshotsAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def create_snapshot(
        self,
        request: Optional[Union[pubsub.CreateSnapshotRequest, dict]] = None,
        *,
        name: Optional[str] = None,
        subscription: Optional[str] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pubsub.Snapshot:
        r"""Creates a snapshot from the requested subscription. Snapshots
        are used in
        `Seek <https://cloud.google.com/pubsub/docs/replay-overview>`__
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.
        If the snapshot already exists, returns ``ALREADY_EXISTS``. If
        the requested subscription doesn't exist, returns ``NOT_FOUND``.
        If the backlog in the subscription is too old -- and the
        resulting snapshot would expire in less than 1 hour -- then
        ``FAILED_PRECONDITION`` is returned. See also the
        ``Snapshot.expire_time`` field. If the name is not provided in
        the request, the server will assign a random name for this
        snapshot on the same project as the subscription, conforming to
        the [resource name format]
        (https://cloud.google.com/pubsub/docs/admin#resource_names). The
        generated name is populated in the returned Snapshot object.
        Note that for REST API requests, you must specify a name in the
        request.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_create_snapshot():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.CreateSnapshotRequest(
                    name="name_value",
                    subscription="subscription_value",
                )

                # Make the request
                response = await client.create_snapshot(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.pubsub_v1.types.CreateSnapshotRequest, dict]]):
                The request object. Request for the ``CreateSnapshot`` method.
            name (:class:`str`):
                Required. User-provided name for this snapshot. If the
                name is not provided in the request, the server will
                assign a random name for this snapshot on the same
                project as the subscription. Note that for REST API
                requests, you must specify a name. See the `resource
                name
                rules <https://cloud.google.com/pubsub/docs/admin#resource_names>`__.
                Format is ``projects/{project}/snapshots/{snap}``.

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            subscription (:class:`str`):
                Required. The subscription whose backlog the snapshot
                retains. Specifically, the created snapshot is
                guaranteed to retain: (a) The existing backlog on the
                subscription. More precisely, this is defined as the
                messages in the subscription's backlog that are
                unacknowledged upon the successful completion of the
                ``CreateSnapshot`` request; as well as: (b) Any messages
                published to the subscription's topic following the
                successful completion of the CreateSnapshot request.
                Format is ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.pubsub_v1.types.Snapshot:
                A snapshot resource. Snapshots are used in
                   [Seek](https://cloud.google.com/pubsub/docs/replay-overview)
                   operations, which allow you to manage message
                   acknowledgments in bulk. That is, you can set the
                   acknowledgment state of messages in an existing
                   subscription to the state captured by a snapshot.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name, subscription])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.CreateSnapshotRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name
        if subscription is not None:
            request.subscription = subscription

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_snapshot,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.ServiceUnavailable,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("name", request.name),)),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def update_snapshot(
        self,
        request: Optional[Union[pubsub.UpdateSnapshotRequest, dict]] = None,
        *,
        snapshot: Optional[pubsub.Snapshot] = None,
        update_mask: Optional[field_mask_pb2.FieldMask] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pubsub.Snapshot:
        r"""Updates an existing snapshot. Snapshots are used in
        `Seek <https://cloud.google.com/pubsub/docs/replay-overview>`__
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_update_snapshot():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.UpdateSnapshotRequest(
                )

                # Make the request
                response = await client.update_snapshot(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.pubsub_v1.types.UpdateSnapshotRequest, dict]]):
                The request object. Request for the UpdateSnapshot
                method.
            snapshot (:class:`google.pubsub_v1.types.Snapshot`):
                Required. The updated snapshot
                object.

                This corresponds to the ``snapshot`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
                Required. Indicates which fields in
                the provided snapshot to update. Must be
                specified and non-empty.

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.pubsub_v1.types.Snapshot:
                A snapshot resource. Snapshots are used in
                   [Seek](https://cloud.google.com/pubsub/docs/replay-overview)
                   operations, which allow you to manage message
                   acknowledgments in bulk. That is, you can set the
                   acknowledgment state of messages in an existing
                   subscription to the state captured by a snapshot.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([snapshot, update_mask])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.UpdateSnapshotRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if snapshot is not None:
            request.snapshot = snapshot
        if update_mask is not None:
            request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_snapshot,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.ServiceUnavailable,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("snapshot.name", request.snapshot.name),)
            ),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def delete_snapshot(
        self,
        request: Optional[Union[pubsub.DeleteSnapshotRequest, dict]] = None,
        *,
        snapshot: Optional[str] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> None:
        r"""Removes an existing snapshot. Snapshots are used in [Seek]
        (https://cloud.google.com/pubsub/docs/replay-overview)
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.
        When the snapshot is deleted, all messages retained in the
        snapshot are immediately dropped. After a snapshot is deleted, a
        new one may be created with the same name, but the new one has
        no association with the old snapshot or its subscription, unless
        the same subscription is specified.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_delete_snapshot():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.DeleteSnapshotRequest(
                    snapshot="snapshot_value",
                )

                # Make the request
                await client.delete_snapshot(request=request)

        Args:
            request (Optional[Union[google.pubsub_v1.types.DeleteSnapshotRequest, dict]]):
                The request object. Request for the ``DeleteSnapshot`` method.
            snapshot (:class:`str`):
                Required. The name of the snapshot to delete. Format is
                ``projects/{project}/snapshots/{snap}``.

                This corresponds to the ``snapshot`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([snapshot])
        if request is not None and has_flattened_params:
            raise ValueError(
                "If the `request` argument is set, then none of "
                "the individual field arguments should be set."
            )

        request = pubsub.DeleteSnapshotRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if snapshot is not None:
            request.snapshot = snapshot

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_snapshot,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.ServiceUnavailable,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("snapshot", request.snapshot),)),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def seek(
        self,
        request: Optional[Union[pubsub.SeekRequest, dict]] = None,
        *,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pubsub.SeekResponse:
        r"""Seeks an existing subscription to a point in time or to a given
        snapshot, whichever is provided in the request. Snapshots are
        used in [Seek]
        (https://cloud.google.com/pubsub/docs/replay-overview)
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.
        Note that both the subscription and the snapshot must be on the
        same topic.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google import pubsub_v1

            async def sample_seek():
                # Create a client
                client = pubsub_v1.SubscriberAsyncClient()

                # Initialize request argument(s)
                request = pubsub_v1.SeekRequest(
                    subscription="subscription_value",
                )

                # Make the request
                response = await client.seek(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.pubsub_v1.types.SeekRequest, dict]]):
                The request object. Request for the ``Seek`` method.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.pubsub_v1.types.SeekResponse:
                Response for the Seek method (this response is empty).
        """
        # Create or coerce a protobuf request object.
        request = pubsub.SeekRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.seek,
            default_retry=retries.Retry(
                initial=0.1,
                maximum=60.0,
                multiplier=1.3,
                predicate=retries.if_exception_type(
                    core_exceptions.Aborted,
                    core_exceptions.ServiceUnavailable,
                    core_exceptions.Unknown,
                ),
                deadline=60.0,
            ),
            default_timeout=60.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def set_iam_policy(
        self,
        request: Optional[iam_policy_pb2.SetIamPolicyRequest] = None,
        *,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> policy_pb2.Policy:
        r"""Sets the IAM access control policy on the specified function.

        Replaces any existing policy.

        Args:
            request (:class:`~.policy_pb2.SetIamPolicyRequest`):
                The request object. Request message for `SetIamPolicy`
                method.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        Returns:
            ~.policy_pb2.Policy:
                Defines an Identity and Access Management (IAM) policy.
                It is used to specify access control policies for Cloud
                Platform resources.
                A ``Policy`` is a collection of ``bindings``. A
                ``binding`` binds one or more ``members`` to a single
                ``role``. Members can be user accounts, service
                accounts, Google groups, and domains (such as G Suite).
                A ``role`` is a named list of permissions (defined by
                IAM or configured by users). A ``binding`` can
                optionally specify a ``condition``, which is a logic
                expression that further constrains the role binding
                based on attributes about the request and/or target
                resource.

                **JSON Example**

                ::
                    {
                      "bindings": [
                        {
                          "role": "roles/resourcemanager.organizationAdmin",
                          "members": [
                            "user:mike@example.com",
                            "group:admins@example.com",
                            "domain:google.com",
                            "serviceAccount:my-project-id@appspot.gserviceaccount.com"
                          ]
                        },
                        {
                          "role": "roles/resourcemanager.organizationViewer",
                          "members": ["user:eve@example.com"],
                          "condition": {
                            "title": "expirable access",
                            "description": "Does not grant access after Sep 2020",
                            "expression": "request.time <
                            timestamp('2020-10-01T00:00:00.000Z')",
                          }
                        }
                      ]
                    }

                **YAML Example**

                ::

                    bindings:
                    - members:
                      - user:mike@example.com
                      - group:admins@example.com
                      - domain:google.com
                      - serviceAccount:my-project-id@appspot.gserviceaccount.com
                      role: roles/resourcemanager.organizationAdmin
                    - members:
                      - user:eve@example.com
                      role: roles/resourcemanager.organizationViewer
                      condition:
                        title: expirable access
                        description: Does not grant access after Sep 2020
                        expression: request.time < timestamp('2020-10-01T00:00:00.000Z')

                For a description of IAM and its features, see the `IAM
                developer's
                guide <https://cloud.google.com/iam/docs>`__.
        """
        # Create or coerce a protobuf request object.

        # The request isn't a proto-plus wrapped type,
        # so it must be constructed via keyword expansion.
        if isinstance(request, dict):
            request = iam_policy_pb2.SetIamPolicyRequest(**request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.set_iam_policy,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("resource", request.resource),)),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def get_iam_policy(
        self,
        request: Optional[iam_policy_pb2.GetIamPolicyRequest] = None,
        *,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> policy_pb2.Policy:
        r"""Gets the IAM access control policy for a function.

        Returns an empty policy if the function exists and does
        not have a policy set.

        Args:
            request (:class:`~.iam_policy_pb2.GetIamPolicyRequest`):
                The request object. Request message for `GetIamPolicy`
                method.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        Returns:
            ~.policy_pb2.Policy:
                Defines an Identity and Access Management (IAM) policy.
                It is used to specify access control policies for Cloud
                Platform resources.
                A ``Policy`` is a collection of ``bindings``. A
                ``binding`` binds one or more ``members`` to a single
                ``role``. Members can be user accounts, service
                accounts, Google groups, and domains (such as G Suite).
                A ``role`` is a named list of permissions (defined by
                IAM or configured by users). A ``binding`` can
                optionally specify a ``condition``, which is a logic
                expression that further constrains the role binding
                based on attributes about the request and/or target
                resource.

                **JSON Example**

                ::

                    {
                      "bindings": [
                        {
                          "role": "roles/resourcemanager.organizationAdmin",
                          "members": [
                            "user:mike@example.com",
                            "group:admins@example.com",
                            "domain:google.com",
                            "serviceAccount:my-project-id@appspot.gserviceaccount.com"
                          ]
                        },
                        {
                          "role": "roles/resourcemanager.organizationViewer",
                          "members": ["user:eve@example.com"],
                          "condition": {
                            "title": "expirable access",
                            "description": "Does not grant access after Sep 2020",
                            "expression": "request.time <
                            timestamp('2020-10-01T00:00:00.000Z')",
                          }
                        }
                      ]
                    }

                **YAML Example**

                ::

                    bindings:
                    - members:
                      - user:mike@example.com
                      - group:admins@example.com
                      - domain:google.com
                      - serviceAccount:my-project-id@appspot.gserviceaccount.com
                      role: roles/resourcemanager.organizationAdmin
                    - members:
                      - user:eve@example.com
                      role: roles/resourcemanager.organizationViewer
                      condition:
                        title: expirable access
                        description: Does not grant access after Sep 2020
                        expression: request.time < timestamp('2020-10-01T00:00:00.000Z')

                For a description of IAM and its features, see the `IAM
                developer's
                guide <https://cloud.google.com/iam/docs>`__.
        """
        # Create or coerce a protobuf request object.

        # The request isn't a proto-plus wrapped type,
        # so it must be constructed via keyword expansion.
        if isinstance(request, dict):
            request = iam_policy_pb2.GetIamPolicyRequest(**request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_iam_policy,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("resource", request.resource),)),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def test_iam_permissions(
        self,
        request: Optional[iam_policy_pb2.TestIamPermissionsRequest] = None,
        *,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> iam_policy_pb2.TestIamPermissionsResponse:
        r"""Tests the specified permissions against the IAM access control
            policy for a function.

        If the function does not exist, this will
        return an empty set of permissions, not a NOT_FOUND error.

        Args:
            request (:class:`~.iam_policy_pb2.TestIamPermissionsRequest`):
                The request object. Request message for
                `TestIamPermissions` method.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        Returns:
            ~iam_policy_pb2.PolicyTestIamPermissionsResponse:
                Response message for ``TestIamPermissions`` method.
        """
        # Create or coerce a protobuf request object.

        # The request isn't a proto-plus wrapped type,
        # so it must be constructed via keyword expansion.
        if isinstance(request, dict):
            request = iam_policy_pb2.TestIamPermissionsRequest(**request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.test_iam_permissions,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("resource", request.resource),)),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def __aenter__(self) -> "SubscriberAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.transport.close()


DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(
    client_library_version=package_version.__version__
)


__all__ = ("SubscriberAsyncClient",)
