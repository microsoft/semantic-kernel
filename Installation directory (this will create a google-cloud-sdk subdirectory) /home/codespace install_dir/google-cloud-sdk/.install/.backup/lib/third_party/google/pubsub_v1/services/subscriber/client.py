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
import os
import re
from typing import (
    Dict,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Iterable,
    Iterator,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

import warnings
from google.pubsub_v1 import gapic_version as package_version

from google.api_core import client_options as client_options_lib
from google.api_core import exceptions as core_exceptions
from google.api_core import gapic_v1
from google.api_core import retry as retries
from google.auth import credentials as ga_credentials  # type: ignore
from google.auth.transport import mtls  # type: ignore
from google.auth.transport.grpc import SslCredentials  # type: ignore
from google.auth.exceptions import MutualTLSChannelError  # type: ignore
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

import grpc
from .transports.base import SubscriberTransport, DEFAULT_CLIENT_INFO
from .transports.grpc import SubscriberGrpcTransport
from .transports.grpc_asyncio import SubscriberGrpcAsyncIOTransport
from .transports.rest import SubscriberRestTransport


class SubscriberClientMeta(type):
    """Metaclass for the Subscriber client.

    This provides class-level methods for building and retrieving
    support objects (e.g. transport) without polluting the client instance
    objects.
    """

    _transport_registry = OrderedDict()  # type: Dict[str, Type[SubscriberTransport]]
    _transport_registry["grpc"] = SubscriberGrpcTransport
    _transport_registry["grpc_asyncio"] = SubscriberGrpcAsyncIOTransport
    _transport_registry["rest"] = SubscriberRestTransport

    def get_transport_class(
        cls,
        label: Optional[str] = None,
    ) -> Type[SubscriberTransport]:
        """Returns an appropriate transport class.

        Args:
            label: The name of the desired transport. If none is
                provided, then the first transport in the registry is used.

        Returns:
            The transport class to use.
        """
        # If a specific transport is requested, return that one.
        if label:
            return cls._transport_registry[label]

        # No transport is requested; return the default (that is, the first one
        # in the dictionary).
        return next(iter(cls._transport_registry.values()))


class SubscriberClient(metaclass=SubscriberClientMeta):
    """The service that an application uses to manipulate subscriptions and
    to consume messages from a subscription via the ``Pull`` method or
    by establishing a bi-directional stream using the ``StreamingPull``
    method.
    """

    @staticmethod
    def _get_default_mtls_endpoint(api_endpoint):
        """Converts api endpoint to mTLS endpoint.

        Convert "*.sandbox.googleapis.com" and "*.googleapis.com" to
        "*.mtls.sandbox.googleapis.com" and "*.mtls.googleapis.com" respectively.
        Args:
            api_endpoint (Optional[str]): the api endpoint to convert.
        Returns:
            str: converted mTLS api endpoint.
        """
        if not api_endpoint:
            return api_endpoint

        mtls_endpoint_re = re.compile(
            r"(?P<name>[^.]+)(?P<mtls>\.mtls)?(?P<sandbox>\.sandbox)?(?P<googledomain>\.googleapis\.com)?"
        )

        m = mtls_endpoint_re.match(api_endpoint)
        name, mtls, sandbox, googledomain = m.groups()
        if mtls or not googledomain:
            return api_endpoint

        if sandbox:
            return api_endpoint.replace(
                "sandbox.googleapis.com", "mtls.sandbox.googleapis.com"
            )

        return api_endpoint.replace(".googleapis.com", ".mtls.googleapis.com")

    # The scopes needed to make gRPC calls to all of the methods defined in
    # this service
    _DEFAULT_SCOPES = (
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/pubsub",
    )

    SERVICE_ADDRESS = "pubsub.googleapis.com:443"
    """The default address of the service."""

    DEFAULT_ENDPOINT = "pubsub.googleapis.com"
    DEFAULT_MTLS_ENDPOINT = _get_default_mtls_endpoint.__func__(  # type: ignore
        DEFAULT_ENDPOINT
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
            SubscriberClient: The constructed client.
        """
        credentials = service_account.Credentials.from_service_account_info(info)
        kwargs["credentials"] = credentials
        return cls(*args, **kwargs)

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
            SubscriberClient: The constructed client.
        """
        credentials = service_account.Credentials.from_service_account_file(filename)
        kwargs["credentials"] = credentials
        return cls(*args, **kwargs)

    from_service_account_json = from_service_account_file

    @property
    def transport(self) -> SubscriberTransport:
        """Returns the transport used by the client instance.

        Returns:
            SubscriberTransport: The transport used by the client
                instance.
        """
        return self._transport

    @staticmethod
    def snapshot_path(
        project: str,
        snapshot: str,
    ) -> str:
        """Returns a fully-qualified snapshot string."""
        return "projects/{project}/snapshots/{snapshot}".format(
            project=project,
            snapshot=snapshot,
        )

    @staticmethod
    def parse_snapshot_path(path: str) -> Dict[str, str]:
        """Parses a snapshot path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/snapshots/(?P<snapshot>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def subscription_path(
        project: str,
        subscription: str,
    ) -> str:
        """Returns a fully-qualified subscription string."""
        return "projects/{project}/subscriptions/{subscription}".format(
            project=project,
            subscription=subscription,
        )

    @staticmethod
    def parse_subscription_path(path: str) -> Dict[str, str]:
        """Parses a subscription path into its component segments."""
        m = re.match(
            r"^projects/(?P<project>.+?)/subscriptions/(?P<subscription>.+?)$", path
        )
        return m.groupdict() if m else {}

    @staticmethod
    def topic_path(
        project: str,
        topic: str,
    ) -> str:
        """Returns a fully-qualified topic string."""
        return "projects/{project}/topics/{topic}".format(
            project=project,
            topic=topic,
        )

    @staticmethod
    def parse_topic_path(path: str) -> Dict[str, str]:
        """Parses a topic path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/topics/(?P<topic>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def common_billing_account_path(
        billing_account: str,
    ) -> str:
        """Returns a fully-qualified billing_account string."""
        return "billingAccounts/{billing_account}".format(
            billing_account=billing_account,
        )

    @staticmethod
    def parse_common_billing_account_path(path: str) -> Dict[str, str]:
        """Parse a billing_account path into its component segments."""
        m = re.match(r"^billingAccounts/(?P<billing_account>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def common_folder_path(
        folder: str,
    ) -> str:
        """Returns a fully-qualified folder string."""
        return "folders/{folder}".format(
            folder=folder,
        )

    @staticmethod
    def parse_common_folder_path(path: str) -> Dict[str, str]:
        """Parse a folder path into its component segments."""
        m = re.match(r"^folders/(?P<folder>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def common_organization_path(
        organization: str,
    ) -> str:
        """Returns a fully-qualified organization string."""
        return "organizations/{organization}".format(
            organization=organization,
        )

    @staticmethod
    def parse_common_organization_path(path: str) -> Dict[str, str]:
        """Parse a organization path into its component segments."""
        m = re.match(r"^organizations/(?P<organization>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def common_project_path(
        project: str,
    ) -> str:
        """Returns a fully-qualified project string."""
        return "projects/{project}".format(
            project=project,
        )

    @staticmethod
    def parse_common_project_path(path: str) -> Dict[str, str]:
        """Parse a project path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def common_location_path(
        project: str,
        location: str,
    ) -> str:
        """Returns a fully-qualified location string."""
        return "projects/{project}/locations/{location}".format(
            project=project,
            location=location,
        )

    @staticmethod
    def parse_common_location_path(path: str) -> Dict[str, str]:
        """Parse a location path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/locations/(?P<location>.+?)$", path)
        return m.groupdict() if m else {}

    @classmethod
    def get_mtls_endpoint_and_cert_source(
        cls, client_options: Optional[client_options_lib.ClientOptions] = None
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
        if client_options is None:
            client_options = client_options_lib.ClientOptions()
        use_client_cert = os.getenv("GOOGLE_API_USE_CLIENT_CERTIFICATE", "false")
        use_mtls_endpoint = os.getenv("GOOGLE_API_USE_MTLS_ENDPOINT", "auto")
        if use_client_cert not in ("true", "false"):
            raise ValueError(
                "Environment variable `GOOGLE_API_USE_CLIENT_CERTIFICATE` must be either `true` or `false`"
            )
        if use_mtls_endpoint not in ("auto", "never", "always"):
            raise MutualTLSChannelError(
                "Environment variable `GOOGLE_API_USE_MTLS_ENDPOINT` must be `never`, `auto` or `always`"
            )

        # Figure out the client cert source to use.
        client_cert_source = None
        if use_client_cert == "true":
            if client_options.client_cert_source:
                client_cert_source = client_options.client_cert_source
            elif mtls.has_default_client_cert_source():
                client_cert_source = mtls.default_client_cert_source()

        # Figure out which api endpoint to use.
        if client_options.api_endpoint is not None:
            api_endpoint = client_options.api_endpoint
        elif use_mtls_endpoint == "always" or (
            use_mtls_endpoint == "auto" and client_cert_source
        ):
            api_endpoint = cls.DEFAULT_MTLS_ENDPOINT
        else:
            api_endpoint = cls.DEFAULT_ENDPOINT

        return api_endpoint, client_cert_source

    def __init__(
        self,
        *,
        credentials: Optional[ga_credentials.Credentials] = None,
        transport: Optional[Union[str, SubscriberTransport]] = None,
        client_options: Optional[Union[client_options_lib.ClientOptions, dict]] = None,
        client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
    ) -> None:
        """Instantiates the subscriber client.

        Args:
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
            transport (Union[str, SubscriberTransport]): The
                transport to use. If set to None, a transport is chosen
                automatically.
            client_options (Optional[Union[google.api_core.client_options.ClientOptions, dict]]): Custom options for the
                client. It won't take effect if a ``transport`` instance is provided.
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
            client_info (google.api_core.gapic_v1.client_info.ClientInfo):
                The client info used to send a user-agent string along with
                API requests. If ``None``, then default info will be used.
                Generally, you only need to set this if you're developing
                your own client library.

        Raises:
            google.auth.exceptions.MutualTLSChannelError: If mutual TLS transport
                creation failed for any reason.
        """
        if isinstance(client_options, dict):
            client_options = client_options_lib.from_dict(client_options)
        if client_options is None:
            client_options = client_options_lib.ClientOptions()
        client_options = cast(client_options_lib.ClientOptions, client_options)

        api_endpoint, client_cert_source_func = self.get_mtls_endpoint_and_cert_source(
            client_options
        )

        api_key_value = getattr(client_options, "api_key", None)
        if api_key_value and credentials:
            raise ValueError(
                "client_options.api_key and credentials are mutually exclusive"
            )

        # Save or instantiate the transport.
        # Ordinarily, we provide the transport, but allowing a custom transport
        # instance provides an extensibility point for unusual situations.
        if isinstance(transport, SubscriberTransport):
            # transport is a SubscriberTransport instance.
            if credentials or client_options.credentials_file or api_key_value:
                raise ValueError(
                    "When providing a transport instance, "
                    "provide its credentials directly."
                )
            if client_options.scopes:
                raise ValueError(
                    "When providing a transport instance, provide its scopes "
                    "directly."
                )
            self._transport = transport
        else:
            import google.auth._default  # type: ignore

            if api_key_value and hasattr(
                google.auth._default, "get_api_key_credentials"
            ):
                credentials = google.auth._default.get_api_key_credentials(
                    api_key_value
                )

            Transport = type(self).get_transport_class(transport)

            emulator_host = os.environ.get("PUBSUB_EMULATOR_HOST")
            if emulator_host:
                if issubclass(Transport, type(self)._transport_registry["grpc"]):
                    channel = grpc.insecure_channel(target=emulator_host)
                else:
                    channel = grpc.aio.insecure_channel(target=emulator_host)
                Transport = functools.partial(Transport, channel=channel)

            self._transport = Transport(
                credentials=credentials,
                credentials_file=client_options.credentials_file,
                host=api_endpoint,
                scopes=client_options.scopes,
                client_cert_source_for_mtls=client_cert_source_func,
                quota_project_id=client_options.quota_project_id,
                client_info=client_info,
                always_use_jwt_access=True,
                api_audience=client_options.api_audience,
            )

    def create_subscription(
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

            def sample_create_subscription():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.Subscription(
                    name="name_value",
                    topic="topic_value",
                )

                # Make the request
                response = client.create_subscription(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[google.pubsub_v1.types.Subscription, dict]):
                The request object. A subscription resource. If none of ``push_config``,
                ``bigquery_config``, or ``cloud_storage_config`` is set,
                then the subscriber will pull and ack messages using API
                methods. At most one of these fields may be set.
            name (str):
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
            topic (str):
                Required. The name of the topic from which this
                subscription is receiving messages. Format is
                ``projects/{project}/topics/{topic}``. The value of this
                field will be ``_deleted-topic_`` if the topic has been
                deleted.

                This corresponds to the ``topic`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            push_config (google.pubsub_v1.types.PushConfig):
                If push delivery is used with this
                subscription, this field is used to
                configure it.

                This corresponds to the ``push_config`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            ack_deadline_seconds (int):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.Subscription.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.Subscription):
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
        rpc = self._transport._wrapped_methods[self._transport.create_subscription]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("name", request.name),)),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def get_subscription(
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

            def sample_get_subscription():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.GetSubscriptionRequest(
                    subscription="subscription_value",
                )

                # Make the request
                response = client.get_subscription(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[google.pubsub_v1.types.GetSubscriptionRequest, dict]):
                The request object. Request for the GetSubscription
                method.
            subscription (str):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.GetSubscriptionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.GetSubscriptionRequest):
            request = pubsub.GetSubscriptionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if subscription is not None:
                request.subscription = subscription

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.get_subscription]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def update_subscription(
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

            def sample_update_subscription():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                subscription = pubsub_v1.Subscription()
                subscription.name = "name_value"
                subscription.topic = "topic_value"

                request = pubsub_v1.UpdateSubscriptionRequest(
                    subscription=subscription,
                )

                # Make the request
                response = client.update_subscription(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[google.pubsub_v1.types.UpdateSubscriptionRequest, dict]):
                The request object. Request for the UpdateSubscription
                method.
            subscription (google.pubsub_v1.types.Subscription):
                Required. The updated subscription
                object.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (google.protobuf.field_mask_pb2.FieldMask):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.UpdateSubscriptionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.UpdateSubscriptionRequest):
            request = pubsub.UpdateSubscriptionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if subscription is not None:
                request.subscription = subscription
            if update_mask is not None:
                request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.update_subscription]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription.name", request.subscription.name),)
            ),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def list_subscriptions(
        self,
        request: Optional[Union[pubsub.ListSubscriptionsRequest, dict]] = None,
        *,
        project: Optional[str] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pagers.ListSubscriptionsPager:
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

            def sample_list_subscriptions():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.ListSubscriptionsRequest(
                    project="project_value",
                )

                # Make the request
                page_result = client.list_subscriptions(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[google.pubsub_v1.types.ListSubscriptionsRequest, dict]):
                The request object. Request for the ``ListSubscriptions`` method.
            project (str):
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
            google.pubsub_v1.services.subscriber.pagers.ListSubscriptionsPager:
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.ListSubscriptionsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.ListSubscriptionsRequest):
            request = pubsub.ListSubscriptionsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if project is not None:
                request.project = project

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_subscriptions]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("project", request.project),)),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # This method is paged; wrap the response in a pager, which provides
        # an `__iter__` convenience method.
        response = pagers.ListSubscriptionsPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def delete_subscription(
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

            def sample_delete_subscription():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.DeleteSubscriptionRequest(
                    subscription="subscription_value",
                )

                # Make the request
                client.delete_subscription(request=request)

        Args:
            request (Union[google.pubsub_v1.types.DeleteSubscriptionRequest, dict]):
                The request object. Request for the DeleteSubscription
                method.
            subscription (str):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.DeleteSubscriptionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.DeleteSubscriptionRequest):
            request = pubsub.DeleteSubscriptionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if subscription is not None:
                request.subscription = subscription

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.delete_subscription]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    def modify_ack_deadline(
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

            def sample_modify_ack_deadline():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.ModifyAckDeadlineRequest(
                    subscription="subscription_value",
                    ack_ids=['ack_ids_value1', 'ack_ids_value2'],
                    ack_deadline_seconds=2066,
                )

                # Make the request
                client.modify_ack_deadline(request=request)

        Args:
            request (Union[google.pubsub_v1.types.ModifyAckDeadlineRequest, dict]):
                The request object. Request for the ModifyAckDeadline
                method.
            subscription (str):
                Required. The name of the subscription. Format is
                ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            ack_ids (MutableSequence[str]):
                Required. List of acknowledgment IDs.
                This corresponds to the ``ack_ids`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            ack_deadline_seconds (int):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.ModifyAckDeadlineRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.ModifyAckDeadlineRequest):
            request = pubsub.ModifyAckDeadlineRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if subscription is not None:
                request.subscription = subscription
            if ack_ids is not None:
                request.ack_ids = ack_ids
            if ack_deadline_seconds is not None:
                request.ack_deadline_seconds = ack_deadline_seconds

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.modify_ack_deadline]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    def acknowledge(
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

            def sample_acknowledge():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.AcknowledgeRequest(
                    subscription="subscription_value",
                    ack_ids=['ack_ids_value1', 'ack_ids_value2'],
                )

                # Make the request
                client.acknowledge(request=request)

        Args:
            request (Union[google.pubsub_v1.types.AcknowledgeRequest, dict]):
                The request object. Request for the Acknowledge method.
            subscription (str):
                Required. The subscription whose message is being
                acknowledged. Format is
                ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            ack_ids (MutableSequence[str]):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.AcknowledgeRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.AcknowledgeRequest):
            request = pubsub.AcknowledgeRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if subscription is not None:
                request.subscription = subscription
            if ack_ids is not None:
                request.ack_ids = ack_ids

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.acknowledge]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    def pull(
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

            def sample_pull():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.PullRequest(
                    subscription="subscription_value",
                    max_messages=1277,
                )

                # Make the request
                response = client.pull(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[google.pubsub_v1.types.PullRequest, dict]):
                The request object. Request for the ``Pull`` method.
            subscription (str):
                Required. The subscription from which messages should be
                pulled. Format is
                ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            return_immediately (bool):
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
            max_messages (int):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.PullRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.PullRequest):
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
        rpc = self._transport._wrapped_methods[self._transport.pull]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def streaming_pull(
        self,
        requests: Optional[Iterator[pubsub.StreamingPullRequest]] = None,
        *,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> Iterable[pubsub.StreamingPullResponse]:
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

            def sample_streaming_pull():
                # Create a client
                client = pubsub_v1.SubscriberClient()

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
                stream = client.streaming_pull(requests=request_generator())

                # Handle the response
                for response in stream:
                    print(response)

        Args:
            requests (Iterator[google.pubsub_v1.types.StreamingPullRequest]):
                The request object iterator. Request for the ``StreamingPull`` streaming RPC method.
                This request is used to establish the initial stream as
                well as to stream acknowledgements and ack deadline
                modifications from the client to the server.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            Iterable[google.pubsub_v1.types.StreamingPullResponse]:
                Response for the StreamingPull method. This response is used to stream
                   messages from the server to the client.

        """

        # Wrappers in api-core should not automatically pre-fetch the first
        # stream result, as this breaks the stream when re-opening it.
        # https://github.com/googleapis/python-pubsub/issues/93#issuecomment-630762257
        self._transport.streaming_pull._prefetch_first_result_ = False

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.streaming_pull]

        # Send the request.
        response = rpc(
            requests,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def modify_push_config(
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

            def sample_modify_push_config():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.ModifyPushConfigRequest(
                    subscription="subscription_value",
                )

                # Make the request
                client.modify_push_config(request=request)

        Args:
            request (Union[google.pubsub_v1.types.ModifyPushConfigRequest, dict]):
                The request object. Request for the ModifyPushConfig
                method.
            subscription (str):
                Required. The name of the subscription. Format is
                ``projects/{project}/subscriptions/{sub}``.

                This corresponds to the ``subscription`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            push_config (google.pubsub_v1.types.PushConfig):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.ModifyPushConfigRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.ModifyPushConfigRequest):
            request = pubsub.ModifyPushConfigRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if subscription is not None:
                request.subscription = subscription
            if push_config is not None:
                request.push_config = push_config

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.modify_push_config]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    def get_snapshot(
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

            def sample_get_snapshot():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.GetSnapshotRequest(
                    snapshot="snapshot_value",
                )

                # Make the request
                response = client.get_snapshot(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[google.pubsub_v1.types.GetSnapshotRequest, dict]):
                The request object. Request for the GetSnapshot method.
            snapshot (str):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.GetSnapshotRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.GetSnapshotRequest):
            request = pubsub.GetSnapshotRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if snapshot is not None:
                request.snapshot = snapshot

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.get_snapshot]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("snapshot", request.snapshot),)),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def list_snapshots(
        self,
        request: Optional[Union[pubsub.ListSnapshotsRequest, dict]] = None,
        *,
        project: Optional[str] = None,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> pagers.ListSnapshotsPager:
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

            def sample_list_snapshots():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.ListSnapshotsRequest(
                    project="project_value",
                )

                # Make the request
                page_result = client.list_snapshots(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[google.pubsub_v1.types.ListSnapshotsRequest, dict]):
                The request object. Request for the ``ListSnapshots`` method.
            project (str):
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
            google.pubsub_v1.services.subscriber.pagers.ListSnapshotsPager:
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.ListSnapshotsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.ListSnapshotsRequest):
            request = pubsub.ListSnapshotsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if project is not None:
                request.project = project

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_snapshots]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("project", request.project),)),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # This method is paged; wrap the response in a pager, which provides
        # an `__iter__` convenience method.
        response = pagers.ListSnapshotsPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def create_snapshot(
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

            def sample_create_snapshot():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.CreateSnapshotRequest(
                    name="name_value",
                    subscription="subscription_value",
                )

                # Make the request
                response = client.create_snapshot(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[google.pubsub_v1.types.CreateSnapshotRequest, dict]):
                The request object. Request for the ``CreateSnapshot`` method.
            name (str):
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
            subscription (str):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.CreateSnapshotRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.CreateSnapshotRequest):
            request = pubsub.CreateSnapshotRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name
            if subscription is not None:
                request.subscription = subscription

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.create_snapshot]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("name", request.name),)),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def update_snapshot(
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

            def sample_update_snapshot():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.UpdateSnapshotRequest(
                )

                # Make the request
                response = client.update_snapshot(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[google.pubsub_v1.types.UpdateSnapshotRequest, dict]):
                The request object. Request for the UpdateSnapshot
                method.
            snapshot (google.pubsub_v1.types.Snapshot):
                Required. The updated snapshot
                object.

                This corresponds to the ``snapshot`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (google.protobuf.field_mask_pb2.FieldMask):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.UpdateSnapshotRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.UpdateSnapshotRequest):
            request = pubsub.UpdateSnapshotRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if snapshot is not None:
                request.snapshot = snapshot
            if update_mask is not None:
                request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.update_snapshot]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("snapshot.name", request.snapshot.name),)
            ),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def delete_snapshot(
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

            def sample_delete_snapshot():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.DeleteSnapshotRequest(
                    snapshot="snapshot_value",
                )

                # Make the request
                client.delete_snapshot(request=request)

        Args:
            request (Union[google.pubsub_v1.types.DeleteSnapshotRequest, dict]):
                The request object. Request for the ``DeleteSnapshot`` method.
            snapshot (str):
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

        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.DeleteSnapshotRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.DeleteSnapshotRequest):
            request = pubsub.DeleteSnapshotRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if snapshot is not None:
                request.snapshot = snapshot

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.delete_snapshot]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("snapshot", request.snapshot),)),
        )

        # Send the request.
        rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    def seek(
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

            def sample_seek():
                # Create a client
                client = pubsub_v1.SubscriberClient()

                # Initialize request argument(s)
                request = pubsub_v1.SeekRequest(
                    subscription="subscription_value",
                )

                # Make the request
                response = client.seek(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[google.pubsub_v1.types.SeekRequest, dict]):
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
        # Minor optimization to avoid making a copy if the user passes
        # in a pubsub.SeekRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, pubsub.SeekRequest):
            request = pubsub.SeekRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.seek]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata(
                (("subscription", request.subscription),)
            ),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def __enter__(self) -> "SubscriberClient":
        return self

    def __exit__(self, type, value, traceback):
        """Releases underlying transport's resources.

        .. warning::
            ONLY use as a context manager if the transport is NOT shared
            with other clients! Exiting the with block will CLOSE the transport
            and may cause errors in other clients!
        """
        self.transport.close()

    def set_iam_policy(
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
            request (:class:`~.iam_policy_pb2.SetIamPolicyRequest`):
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
        rpc = gapic_v1.method.wrap_method(
            self._transport.set_iam_policy,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("resource", request.resource),)),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def get_iam_policy(
        self,
        request: Optional[iam_policy_pb2.GetIamPolicyRequest] = None,
        *,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> policy_pb2.Policy:
        r"""Gets the IAM access control policy for a function.

        Returns an empty policy if the function exists and does not have a
        policy set.

        Args:
            request (:class:`~.iam_policy_pb2.GetIamPolicyRequest`):
                The request object. Request message for `GetIamPolicy`
                method.
            retry (google.api_core.retry.Retry): Designation of what errors, if
                any, should be retried.
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
        rpc = gapic_v1.method.wrap_method(
            self._transport.get_iam_policy,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("resource", request.resource),)),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def test_iam_permissions(
        self,
        request: Optional[iam_policy_pb2.TestIamPermissionsRequest] = None,
        *,
        retry: OptionalRetry = gapic_v1.method.DEFAULT,
        timeout: Union[float, object] = gapic_v1.method.DEFAULT,
        metadata: Sequence[Tuple[str, str]] = (),
    ) -> iam_policy_pb2.TestIamPermissionsResponse:
        r"""Tests the specified IAM permissions against the IAM access control
            policy for a function.

        If the function does not exist, this will return an empty set
        of permissions, not a NOT_FOUND error.

        Args:
            request (:class:`~.iam_policy_pb2.TestIamPermissionsRequest`):
                The request object. Request message for
                `TestIamPermissions` method.
            retry (google.api_core.retry.Retry): Designation of what errors,
                 if any, should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        Returns:
            ~.iam_policy_pb2.TestIamPermissionsResponse:
                Response message for ``TestIamPermissions`` method.
        """
        # Create or coerce a protobuf request object.

        # The request isn't a proto-plus wrapped type,
        # so it must be constructed via keyword expansion.
        if isinstance(request, dict):
            request = iam_policy_pb2.TestIamPermissionsRequest(**request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method.wrap_method(
            self._transport.test_iam_permissions,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((("resource", request.resource),)),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response


DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(
    client_library_version=package_version.__version__
)


__all__ = ("SubscriberClient",)
