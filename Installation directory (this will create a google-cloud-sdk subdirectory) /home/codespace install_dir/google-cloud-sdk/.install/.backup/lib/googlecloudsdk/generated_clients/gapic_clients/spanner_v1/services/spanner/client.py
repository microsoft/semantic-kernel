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
import os
import re
from typing import Dict, Mapping, MutableMapping, MutableSequence, Optional, Iterable, Sequence, Tuple, Type, Union, cast

from googlecloudsdk.generated_clients.gapic_clients.spanner_v1 import gapic_version as package_version

from google.api_core import client_options as client_options_lib
from google.api_core import exceptions as core_exceptions
from google.api_core import gapic_v1
from google.api_core import retry as retries
from google.auth import credentials as ga_credentials             # type: ignore
from google.auth.transport import mtls                            # type: ignore
from google.auth.transport.grpc import SslCredentials             # type: ignore
from google.auth.exceptions import MutualTLSChannelError          # type: ignore
from google.oauth2 import service_account                         # type: ignore

try:
    OptionalRetry = Union[retries.Retry, gapic_v1.method._MethodDefault]
except AttributeError:  # pragma: NO COVER
    OptionalRetry = Union[retries.Retry, object]  # type: ignore

from cloudsdk.google.protobuf import struct_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore
from google.rpc import status_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.spanner_v1.services.spanner import pagers
from googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types import commit_response
from googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types import mutation
from googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types import result_set
from googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types import spanner
from googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types import transaction
from .transports.base import SpannerTransport, DEFAULT_CLIENT_INFO
from .transports.grpc import SpannerGrpcTransport
from .transports.grpc_asyncio import SpannerGrpcAsyncIOTransport
from .transports.rest import SpannerRestTransport


class SpannerClientMeta(type):
    """Metaclass for the Spanner client.

    This provides class-level methods for building and retrieving
    support objects (e.g. transport) without polluting the client instance
    objects.
    """
    _transport_registry = OrderedDict()  # type: Dict[str, Type[SpannerTransport]]
    _transport_registry["grpc"] = SpannerGrpcTransport
    _transport_registry["grpc_asyncio"] = SpannerGrpcAsyncIOTransport
    _transport_registry["rest"] = SpannerRestTransport

    def get_transport_class(cls,
            label: Optional[str] = None,
        ) -> Type[SpannerTransport]:
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


class SpannerClient(metaclass=SpannerClientMeta):
    """Cloud Spanner API

    The Cloud Spanner API can be used to manage sessions and execute
    transactions on data stored in Cloud Spanner databases.
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

    DEFAULT_ENDPOINT = "spanner.googleapis.com"
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
            SpannerClient: The constructed client.
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
            SpannerClient: The constructed client.
        """
        credentials = service_account.Credentials.from_service_account_file(
            filename)
        kwargs["credentials"] = credentials
        return cls(*args, **kwargs)

    from_service_account_json = from_service_account_file

    @property
    def transport(self) -> SpannerTransport:
        """Returns the transport used by the client instance.

        Returns:
            SpannerTransport: The transport used by the client
                instance.
        """
        return self._transport

    @staticmethod
    def database_path(project: str,instance: str,database: str,) -> str:
        """Returns a fully-qualified database string."""
        return "projects/{project}/instances/{instance}/databases/{database}".format(project=project, instance=instance, database=database, )

    @staticmethod
    def parse_database_path(path: str) -> Dict[str,str]:
        """Parses a database path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/instances/(?P<instance>.+?)/databases/(?P<database>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def session_path(project: str,instance: str,database: str,session: str,) -> str:
        """Returns a fully-qualified session string."""
        return "projects/{project}/instances/{instance}/databases/{database}/sessions/{session}".format(project=project, instance=instance, database=database, session=session, )

    @staticmethod
    def parse_session_path(path: str) -> Dict[str,str]:
        """Parses a session path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/instances/(?P<instance>.+?)/databases/(?P<database>.+?)/sessions/(?P<session>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def common_billing_account_path(billing_account: str, ) -> str:
        """Returns a fully-qualified billing_account string."""
        return "billingAccounts/{billing_account}".format(billing_account=billing_account, )

    @staticmethod
    def parse_common_billing_account_path(path: str) -> Dict[str,str]:
        """Parse a billing_account path into its component segments."""
        m = re.match(r"^billingAccounts/(?P<billing_account>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def common_folder_path(folder: str, ) -> str:
        """Returns a fully-qualified folder string."""
        return "folders/{folder}".format(folder=folder, )

    @staticmethod
    def parse_common_folder_path(path: str) -> Dict[str,str]:
        """Parse a folder path into its component segments."""
        m = re.match(r"^folders/(?P<folder>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def common_organization_path(organization: str, ) -> str:
        """Returns a fully-qualified organization string."""
        return "organizations/{organization}".format(organization=organization, )

    @staticmethod
    def parse_common_organization_path(path: str) -> Dict[str,str]:
        """Parse a organization path into its component segments."""
        m = re.match(r"^organizations/(?P<organization>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def common_project_path(project: str, ) -> str:
        """Returns a fully-qualified project string."""
        return "projects/{project}".format(project=project, )

    @staticmethod
    def parse_common_project_path(path: str) -> Dict[str,str]:
        """Parse a project path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def common_location_path(project: str, location: str, ) -> str:
        """Returns a fully-qualified location string."""
        return "projects/{project}/locations/{location}".format(project=project, location=location, )

    @staticmethod
    def parse_common_location_path(path: str) -> Dict[str,str]:
        """Parse a location path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/locations/(?P<location>.+?)$", path)
        return m.groupdict() if m else {}

    @classmethod
    def get_mtls_endpoint_and_cert_source(cls, client_options: Optional[client_options_lib.ClientOptions] = None):
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
            raise ValueError("Environment variable `GOOGLE_API_USE_CLIENT_CERTIFICATE` must be either `true` or `false`")
        if use_mtls_endpoint not in ("auto", "never", "always"):
            raise MutualTLSChannelError("Environment variable `GOOGLE_API_USE_MTLS_ENDPOINT` must be `never`, `auto` or `always`")

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
        elif use_mtls_endpoint == "always" or (use_mtls_endpoint == "auto" and client_cert_source):
            api_endpoint = cls.DEFAULT_MTLS_ENDPOINT
        else:
            api_endpoint = cls.DEFAULT_ENDPOINT

        return api_endpoint, client_cert_source

    def __init__(self, *,
            credentials: Optional[ga_credentials.Credentials] = None,
            transport: Optional[Union[str, SpannerTransport]] = None,
            client_options: Optional[Union[client_options_lib.ClientOptions, dict]] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            ) -> None:
        """Instantiates the spanner client.

        Args:
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
            transport (Union[str, SpannerTransport]): The
                transport to use. If set to None, a transport is chosen
                automatically.
                NOTE: "rest" transport functionality is currently in a
                beta state (preview). We welcome your feedback via an
                issue in this library's source repository.
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

        api_endpoint, client_cert_source_func = self.get_mtls_endpoint_and_cert_source(client_options)

        api_key_value = getattr(client_options, "api_key", None)
        if api_key_value and credentials:
            raise ValueError("client_options.api_key and credentials are mutually exclusive")

        # Save or instantiate the transport.
        # Ordinarily, we provide the transport, but allowing a custom transport
        # instance provides an extensibility point for unusual situations.
        if isinstance(transport, SpannerTransport):
            # transport is a SpannerTransport instance.
            if credentials or client_options.credentials_file or api_key_value:
                raise ValueError("When providing a transport instance, "
                                 "provide its credentials directly.")
            if client_options.scopes:
                raise ValueError(
                    "When providing a transport instance, provide its scopes "
                    "directly."
                )
            self._transport = transport
        else:
            import google.auth._default  # type: ignore

            if api_key_value and hasattr(google.auth._default, "get_api_key_credentials"):
                credentials = google.auth._default.get_api_key_credentials(api_key_value)

            Transport = type(self).get_transport_class(transport)
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

    def create_session(self,
            request: Optional[Union[spanner.CreateSessionRequest, dict]] = None,
            *,
            database: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> spanner.Session:
        r"""Creates a new session. A session can be used to perform
        transactions that read and/or modify data in a Cloud Spanner
        database. Sessions are meant to be reused for many consecutive
        transactions.

        Sessions can only execute one transaction at a time. To execute
        multiple concurrent read-write/write-only transactions, create
        multiple sessions. Note that standalone reads and queries use a
        transaction internally, and count toward the one transaction
        limit.

        Active sessions use additional server resources, so it is a good
        idea to delete idle and unneeded sessions. Aside from explicit
        deletes, Cloud Spanner may delete sessions for which no
        operations are sent for more than an hour. If a session is
        deleted, requests to it return ``NOT_FOUND``.

        Idle sessions can be kept alive by sending a trivial SQL query
        periodically, e.g., ``"SELECT 1"``.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_create_session():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.CreateSessionRequest(
                    database="database_value",
                )

                # Make the request
                response = client.create_session(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.CreateSessionRequest, dict]):
                The request object. The request for
                [CreateSession][google.spanner.v1.Spanner.CreateSession].
            database (str):
                Required. The database in which the
                new session is created.

                This corresponds to the ``database`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.Session:
                A session in the Cloud Spanner API.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([database])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.CreateSessionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.CreateSessionRequest):
            request = spanner.CreateSessionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if database is not None:
                request.database = database

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.create_session]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("database", request.database),
            )),
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

    def batch_create_sessions(self,
            request: Optional[Union[spanner.BatchCreateSessionsRequest, dict]] = None,
            *,
            database: Optional[str] = None,
            session_count: Optional[int] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> spanner.BatchCreateSessionsResponse:
        r"""Creates multiple new sessions.

        This API can be used to initialize a session cache on
        the clients. See https://goo.gl/TgSFN2 for best
        practices on session cache management.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_batch_create_sessions():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.BatchCreateSessionsRequest(
                    database="database_value",
                    session_count=1420,
                )

                # Make the request
                response = client.batch_create_sessions(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.BatchCreateSessionsRequest, dict]):
                The request object. The request for
                [BatchCreateSessions][google.spanner.v1.Spanner.BatchCreateSessions].
            database (str):
                Required. The database in which the
                new sessions are created.

                This corresponds to the ``database`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            session_count (int):
                Required. The number of sessions to be created in this
                batch call. The API may return fewer than the requested
                number of sessions. If a specific number of sessions are
                desired, the client can make additional calls to
                BatchCreateSessions (adjusting
                [session_count][google.spanner.v1.BatchCreateSessionsRequest.session_count]
                as necessary).

                This corresponds to the ``session_count`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.BatchCreateSessionsResponse:
                The response for
                   [BatchCreateSessions][google.spanner.v1.Spanner.BatchCreateSessions].

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([database, session_count])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.BatchCreateSessionsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.BatchCreateSessionsRequest):
            request = spanner.BatchCreateSessionsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if database is not None:
                request.database = database
            if session_count is not None:
                request.session_count = session_count

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.batch_create_sessions]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("database", request.database),
            )),
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

    def get_session(self,
            request: Optional[Union[spanner.GetSessionRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> spanner.Session:
        r"""Gets a session. Returns ``NOT_FOUND`` if the session does not
        exist. This is mainly useful for determining whether a session
        is still alive.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_get_session():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.GetSessionRequest(
                    name="name_value",
                )

                # Make the request
                response = client.get_session(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.GetSessionRequest, dict]):
                The request object. The request for
                [GetSession][google.spanner.v1.Spanner.GetSession].
            name (str):
                Required. The name of the session to
                retrieve.

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.Session:
                A session in the Cloud Spanner API.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.GetSessionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.GetSessionRequest):
            request = spanner.GetSessionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.get_session]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    def list_sessions(self,
            request: Optional[Union[spanner.ListSessionsRequest, dict]] = None,
            *,
            database: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListSessionsPager:
        r"""Lists all sessions in a given database.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_list_sessions():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.ListSessionsRequest(
                    database="database_value",
                )

                # Make the request
                page_result = client.list_sessions(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ListSessionsRequest, dict]):
                The request object. The request for
                [ListSessions][google.spanner.v1.Spanner.ListSessions].
            database (str):
                Required. The database in which to
                list sessions.

                This corresponds to the ``database`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.services.spanner.pagers.ListSessionsPager:
                The response for
                [ListSessions][google.spanner.v1.Spanner.ListSessions].

                Iterating over this object will yield results and
                resolve additional pages automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([database])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.ListSessionsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.ListSessionsRequest):
            request = spanner.ListSessionsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if database is not None:
                request.database = database

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_sessions]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("database", request.database),
            )),
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
        response = pagers.ListSessionsPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def delete_session(self,
            request: Optional[Union[spanner.DeleteSessionRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Ends a session, releasing server resources associated
        with it. This will asynchronously trigger cancellation
        of any operations that are running with this session.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_delete_session():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.DeleteSessionRequest(
                    name="name_value",
                )

                # Make the request
                client.delete_session(request=request)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.DeleteSessionRequest, dict]):
                The request object. The request for
                [DeleteSession][google.spanner.v1.Spanner.DeleteSession].
            name (str):
                Required. The name of the session to
                delete.

                This corresponds to the ``name`` field
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
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.DeleteSessionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.DeleteSessionRequest):
            request = spanner.DeleteSessionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.delete_session]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
        )

        # Send the request.
        rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    def execute_sql(self,
            request: Optional[Union[spanner.ExecuteSqlRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> result_set.ResultSet:
        r"""Executes an SQL statement, returning all results in a single
        reply. This method cannot be used to return a result set larger
        than 10 MiB; if the query yields more data than that, the query
        fails with a ``FAILED_PRECONDITION`` error.

        Operations inside read-write transactions might return
        ``ABORTED``. If this occurs, the application should restart the
        transaction from the beginning. See
        [Transaction][google.spanner.v1.Transaction] for more details.

        Larger result sets can be fetched in streaming fashion by
        calling
        [ExecuteStreamingSql][google.spanner.v1.Spanner.ExecuteStreamingSql]
        instead.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_execute_sql():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.ExecuteSqlRequest(
                    session="session_value",
                    sql="sql_value",
                )

                # Make the request
                response = client.execute_sql(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ExecuteSqlRequest, dict]):
                The request object. The request for
                [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql] and
                [ExecuteStreamingSql][google.spanner.v1.Spanner.ExecuteStreamingSql].
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ResultSet:
                Results from [Read][google.spanner.v1.Spanner.Read] or
                   [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql].

        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.ExecuteSqlRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.ExecuteSqlRequest):
            request = spanner.ExecuteSqlRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.execute_sql]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
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

    def execute_streaming_sql(self,
            request: Optional[Union[spanner.ExecuteSqlRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> Iterable[result_set.PartialResultSet]:
        r"""Like [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql], except
        returns the result set as a stream. Unlike
        [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql], there is no
        limit on the size of the returned result set. However, no
        individual row in the result set can exceed 100 MiB, and no
        column value can exceed 10 MiB.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_execute_streaming_sql():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.ExecuteSqlRequest(
                    session="session_value",
                    sql="sql_value",
                )

                # Make the request
                stream = client.execute_streaming_sql(request=request)

                # Handle the response
                for response in stream:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ExecuteSqlRequest, dict]):
                The request object. The request for
                [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql] and
                [ExecuteStreamingSql][google.spanner.v1.Spanner.ExecuteStreamingSql].
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            Iterable[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.PartialResultSet]:
                Partial results from a streaming read
                or SQL query. Streaming reads and SQL
                queries better tolerate large result
                sets, large rows, and large values, but
                are a little trickier to consume.

        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.ExecuteSqlRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.ExecuteSqlRequest):
            request = spanner.ExecuteSqlRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.execute_streaming_sql]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
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

    def execute_batch_dml(self,
            request: Optional[Union[spanner.ExecuteBatchDmlRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> spanner.ExecuteBatchDmlResponse:
        r"""Executes a batch of SQL DML statements. This method allows many
        statements to be run with lower latency than submitting them
        sequentially with
        [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql].

        Statements are executed in sequential order. A request can
        succeed even if a statement fails. The
        [ExecuteBatchDmlResponse.status][google.spanner.v1.ExecuteBatchDmlResponse.status]
        field in the response provides information about the statement
        that failed. Clients must inspect this field to determine
        whether an error occurred.

        Execution stops after the first failed statement; the remaining
        statements are not executed.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_execute_batch_dml():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                statements = spanner_v1.Statement()
                statements.sql = "sql_value"

                request = spanner_v1.ExecuteBatchDmlRequest(
                    session="session_value",
                    statements=statements,
                    seqno=550,
                )

                # Make the request
                response = client.execute_batch_dml(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ExecuteBatchDmlRequest, dict]):
                The request object. The request for
                [ExecuteBatchDml][google.spanner.v1.Spanner.ExecuteBatchDml].
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ExecuteBatchDmlResponse:
                The response for
                   [ExecuteBatchDml][google.spanner.v1.Spanner.ExecuteBatchDml].
                   Contains a list of
                   [ResultSet][google.spanner.v1.ResultSet] messages,
                   one for each DML statement that has successfully
                   executed, in the same order as the statements in the
                   request. If a statement fails, the status in the
                   response body identifies the cause of the failure.

                   To check for DML statements that failed, use the
                   following approach:

                   1. Check the status in the response message. The
                   [google.rpc.Code][google.rpc.Code] enum value OK
                   indicates that all statements were executed
                   successfully. 2. If the status was not OK, check the
                   number of result sets in the response. If the
                   response contains N
                   [ResultSet][google.spanner.v1.ResultSet] messages,
                   then statement N+1 in the request failed.

                   Example 1:

                   -  Request: 5 DML statements, all executed
                      successfully.

                   \* Response: 5
                   [ResultSet][google.spanner.v1.ResultSet] messages,
                   with the status OK.

                   Example 2:

                   -  Request: 5 DML statements. The third statement has
                      a syntax error.

                   \* Response: 2
                   [ResultSet][google.spanner.v1.ResultSet] messages,
                   and a syntax error (INVALID_ARGUMENT) status. The
                   number of [ResultSet][google.spanner.v1.ResultSet]
                   messages indicates that the third statement failed,
                   and the fourth and fifth statements were not
                   executed.

        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.ExecuteBatchDmlRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.ExecuteBatchDmlRequest):
            request = spanner.ExecuteBatchDmlRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.execute_batch_dml]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
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

    def read(self,
            request: Optional[Union[spanner.ReadRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> result_set.ResultSet:
        r"""Reads rows from the database using key lookups and scans, as a
        simple key/value style alternative to
        [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql]. This method
        cannot be used to return a result set larger than 10 MiB; if the
        read matches more data than that, the read fails with a
        ``FAILED_PRECONDITION`` error.

        Reads inside read-write transactions might return ``ABORTED``.
        If this occurs, the application should restart the transaction
        from the beginning. See
        [Transaction][google.spanner.v1.Transaction] for more details.

        Larger result sets can be yielded in streaming fashion by
        calling [StreamingRead][google.spanner.v1.Spanner.StreamingRead]
        instead.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_read():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.ReadRequest(
                    session="session_value",
                    table="table_value",
                    columns=['columns_value1', 'columns_value2'],
                )

                # Make the request
                response = client.read(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ReadRequest, dict]):
                The request object. The request for [Read][google.spanner.v1.Spanner.Read]
                and
                [StreamingRead][google.spanner.v1.Spanner.StreamingRead].
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ResultSet:
                Results from [Read][google.spanner.v1.Spanner.Read] or
                   [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql].

        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.ReadRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.ReadRequest):
            request = spanner.ReadRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.read]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
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

    def streaming_read(self,
            request: Optional[Union[spanner.ReadRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> Iterable[result_set.PartialResultSet]:
        r"""Like [Read][google.spanner.v1.Spanner.Read], except returns the
        result set as a stream. Unlike
        [Read][google.spanner.v1.Spanner.Read], there is no limit on the
        size of the returned result set. However, no individual row in
        the result set can exceed 100 MiB, and no column value can
        exceed 10 MiB.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_streaming_read():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.ReadRequest(
                    session="session_value",
                    table="table_value",
                    columns=['columns_value1', 'columns_value2'],
                )

                # Make the request
                stream = client.streaming_read(request=request)

                # Handle the response
                for response in stream:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ReadRequest, dict]):
                The request object. The request for [Read][google.spanner.v1.Spanner.Read]
                and
                [StreamingRead][google.spanner.v1.Spanner.StreamingRead].
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            Iterable[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.PartialResultSet]:
                Partial results from a streaming read
                or SQL query. Streaming reads and SQL
                queries better tolerate large result
                sets, large rows, and large values, but
                are a little trickier to consume.

        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.ReadRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.ReadRequest):
            request = spanner.ReadRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.streaming_read]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
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

    def begin_transaction(self,
            request: Optional[Union[spanner.BeginTransactionRequest, dict]] = None,
            *,
            session: Optional[str] = None,
            options: Optional[transaction.TransactionOptions] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> transaction.Transaction:
        r"""Begins a new transaction. This step can often be skipped:
        [Read][google.spanner.v1.Spanner.Read],
        [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql] and
        [Commit][google.spanner.v1.Spanner.Commit] can begin a new
        transaction as a side-effect.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_begin_transaction():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.BeginTransactionRequest(
                    session="session_value",
                )

                # Make the request
                response = client.begin_transaction(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.BeginTransactionRequest, dict]):
                The request object. The request for
                [BeginTransaction][google.spanner.v1.Spanner.BeginTransaction].
            session (str):
                Required. The session in which the
                transaction runs.

                This corresponds to the ``session`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            options (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.TransactionOptions):
                Required. Options for the new
                transaction.

                This corresponds to the ``options`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.Transaction:
                A transaction.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([session, options])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.BeginTransactionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.BeginTransactionRequest):
            request = spanner.BeginTransactionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if session is not None:
                request.session = session
            if options is not None:
                request.options = options

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.begin_transaction]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
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

    def commit(self,
            request: Optional[Union[spanner.CommitRequest, dict]] = None,
            *,
            session: Optional[str] = None,
            transaction_id: Optional[bytes] = None,
            mutations: Optional[MutableSequence[mutation.Mutation]] = None,
            single_use_transaction: Optional[transaction.TransactionOptions] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> commit_response.CommitResponse:
        r"""Commits a transaction. The request includes the mutations to be
        applied to rows in the database.

        ``Commit`` might return an ``ABORTED`` error. This can occur at
        any time; commonly, the cause is conflicts with concurrent
        transactions. However, it can also happen for a variety of other
        reasons. If ``Commit`` returns ``ABORTED``, the caller should
        re-attempt the transaction from the beginning, re-using the same
        session.

        On very rare occasions, ``Commit`` might return ``UNKNOWN``.
        This can happen, for example, if the client job experiences a 1+
        hour networking failure. At that point, Cloud Spanner has lost
        track of the transaction outcome and we recommend that you
        perform another read from the database to see the state of
        things as they are now.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_commit():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.CommitRequest(
                    transaction_id=b'transaction_id_blob',
                    session="session_value",
                )

                # Make the request
                response = client.commit(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.CommitRequest, dict]):
                The request object. The request for
                [Commit][google.spanner.v1.Spanner.Commit].
            session (str):
                Required. The session in which the
                transaction to be committed is running.

                This corresponds to the ``session`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            transaction_id (bytes):
                Commit a previously-started
                transaction.

                This corresponds to the ``transaction_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            mutations (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.Mutation]):
                The mutations to be executed when
                this transaction commits. All mutations
                are applied atomically, in the order
                they appear in this list.

                This corresponds to the ``mutations`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            single_use_transaction (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.TransactionOptions):
                Execute mutations in a temporary transaction. Note that
                unlike commit of a previously-started transaction,
                commit with a temporary transaction is non-idempotent.
                That is, if the ``CommitRequest`` is sent to Cloud
                Spanner more than once (for instance, due to retries in
                the application, or in the transport library), it is
                possible that the mutations are executed more than once.
                If this is undesirable, use
                [BeginTransaction][google.spanner.v1.Spanner.BeginTransaction]
                and [Commit][google.spanner.v1.Spanner.Commit] instead.

                This corresponds to the ``single_use_transaction`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.CommitResponse:
                The response for
                [Commit][google.spanner.v1.Spanner.Commit].

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([session, transaction_id, mutations, single_use_transaction])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.CommitRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.CommitRequest):
            request = spanner.CommitRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if session is not None:
                request.session = session
            if transaction_id is not None:
                request.transaction_id = transaction_id
            if mutations is not None:
                request.mutations = mutations
            if single_use_transaction is not None:
                request.single_use_transaction = single_use_transaction

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.commit]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
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

    def rollback(self,
            request: Optional[Union[spanner.RollbackRequest, dict]] = None,
            *,
            session: Optional[str] = None,
            transaction_id: Optional[bytes] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Rolls back a transaction, releasing any locks it holds. It is a
        good idea to call this for any transaction that includes one or
        more [Read][google.spanner.v1.Spanner.Read] or
        [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql] requests and
        ultimately decides not to commit.

        ``Rollback`` returns ``OK`` if it successfully aborts the
        transaction, the transaction was already aborted, or the
        transaction is not found. ``Rollback`` never returns
        ``ABORTED``.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_rollback():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.RollbackRequest(
                    session="session_value",
                    transaction_id=b'transaction_id_blob',
                )

                # Make the request
                client.rollback(request=request)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.RollbackRequest, dict]):
                The request object. The request for
                [Rollback][google.spanner.v1.Spanner.Rollback].
            session (str):
                Required. The session in which the
                transaction to roll back is running.

                This corresponds to the ``session`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            transaction_id (bytes):
                Required. The transaction to roll
                back.

                This corresponds to the ``transaction_id`` field
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
        has_flattened_params = any([session, transaction_id])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.RollbackRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.RollbackRequest):
            request = spanner.RollbackRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if session is not None:
                request.session = session
            if transaction_id is not None:
                request.transaction_id = transaction_id

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.rollback]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
        )

        # Send the request.
        rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    def partition_query(self,
            request: Optional[Union[spanner.PartitionQueryRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> spanner.PartitionResponse:
        r"""Creates a set of partition tokens that can be used to execute a
        query operation in parallel. Each of the returned partition
        tokens can be used by
        [ExecuteStreamingSql][google.spanner.v1.Spanner.ExecuteStreamingSql]
        to specify a subset of the query result to read. The same
        session and read-only transaction must be used by the
        PartitionQueryRequest used to create the partition tokens and
        the ExecuteSqlRequests that use the partition tokens.

        Partition tokens become invalid when the session used to create
        them is deleted, is idle for too long, begins a new transaction,
        or becomes too old. When any of these happen, it is not possible
        to resume the query, and the whole operation must be restarted
        from the beginning.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_partition_query():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.PartitionQueryRequest(
                    session="session_value",
                    sql="sql_value",
                )

                # Make the request
                response = client.partition_query(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.PartitionQueryRequest, dict]):
                The request object. The request for
                [PartitionQuery][google.spanner.v1.Spanner.PartitionQuery]
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.PartitionResponse:
                The response for [PartitionQuery][google.spanner.v1.Spanner.PartitionQuery]
                   or
                   [PartitionRead][google.spanner.v1.Spanner.PartitionRead]

        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.PartitionQueryRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.PartitionQueryRequest):
            request = spanner.PartitionQueryRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.partition_query]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
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

    def partition_read(self,
            request: Optional[Union[spanner.PartitionReadRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> spanner.PartitionResponse:
        r"""Creates a set of partition tokens that can be used to execute a
        read operation in parallel. Each of the returned partition
        tokens can be used by
        [StreamingRead][google.spanner.v1.Spanner.StreamingRead] to
        specify a subset of the read result to read. The same session
        and read-only transaction must be used by the
        PartitionReadRequest used to create the partition tokens and the
        ReadRequests that use the partition tokens. There are no
        ordering guarantees on rows returned among the returned
        partition tokens, or even within each individual StreamingRead
        call issued with a partition_token.

        Partition tokens become invalid when the session used to create
        them is deleted, is idle for too long, begins a new transaction,
        or becomes too old. When any of these happen, it is not possible
        to resume the read, and the whole operation must be restarted
        from the beginning.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_partition_read():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                request = spanner_v1.PartitionReadRequest(
                    session="session_value",
                    table="table_value",
                )

                # Make the request
                response = client.partition_read(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.PartitionReadRequest, dict]):
                The request object. The request for
                [PartitionRead][google.spanner.v1.Spanner.PartitionRead]
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.PartitionResponse:
                The response for [PartitionQuery][google.spanner.v1.Spanner.PartitionQuery]
                   or
                   [PartitionRead][google.spanner.v1.Spanner.PartitionRead]

        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.PartitionReadRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.PartitionReadRequest):
            request = spanner.PartitionReadRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.partition_read]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
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

    def batch_write(self,
            request: Optional[Union[spanner.BatchWriteRequest, dict]] = None,
            *,
            session: Optional[str] = None,
            mutation_groups: Optional[MutableSequence[spanner.BatchWriteRequest.MutationGroup]] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> Iterable[spanner.BatchWriteResponse]:
        r"""Batches the supplied mutation groups in a collection
        of efficient transactions. All mutations in a group are
        committed atomically. However, mutations across groups
        can be committed non-atomically in an unspecified order
        and thus, they must be independent of each other.
        Partial failure is possible, i.e., some groups may have
        been committed successfully, while some may have failed.
        The results of individual batches are streamed into the
        response as the batches are applied.

        BatchWrite requests are not replay protected, meaning
        that each mutation group may be applied more than once.
        Replays of non-idempotent mutations may have undesirable
        effects. For example, replays of an insert mutation may
        produce an already exists error or if you use generated
        or commit timestamp-based keys, it may result in
        additional rows being added to the mutation's table. We
        recommend structuring your mutation groups to be
        idempotent to avoid this issue.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import spanner_v1

            def sample_batch_write():
                # Create a client
                client = spanner_v1.SpannerClient()

                # Initialize request argument(s)
                mutation_groups = spanner_v1.MutationGroup()
                mutation_groups.mutations.insert.table = "table_value"

                request = spanner_v1.BatchWriteRequest(
                    session="session_value",
                    mutation_groups=mutation_groups,
                )

                # Make the request
                stream = client.batch_write(request=request)

                # Handle the response
                for response in stream:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.BatchWriteRequest, dict]):
                The request object. The request for
                [BatchWrite][google.spanner.v1.Spanner.BatchWrite].
            session (str):
                Required. The session in which the
                batch request is to be run.

                This corresponds to the ``session`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            mutation_groups (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.BatchWriteRequest.MutationGroup]):
                Required. The groups of mutations to
                be applied.

                This corresponds to the ``mutation_groups`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            Iterable[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.BatchWriteResponse]:
                The result of applying a batch of
                mutations.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([session, mutation_groups])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a spanner.BatchWriteRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, spanner.BatchWriteRequest):
            request = spanner.BatchWriteRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if session is not None:
                request.session = session
            if mutation_groups is not None:
                request.mutation_groups = mutation_groups

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.batch_write]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("session", request.session),
            )),
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

    def __enter__(self) -> "SpannerClient":
        return self

    def __exit__(self, type, value, traceback):
        """Releases underlying transport's resources.

        .. warning::
            ONLY use as a context manager if the transport is NOT shared
            with other clients! Exiting the with block will CLOSE the transport
            and may cause errors in other clients!
        """
        self.transport.close()







DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(gapic_version=package_version.__version__)


__all__ = (
    "SpannerClient",
)
