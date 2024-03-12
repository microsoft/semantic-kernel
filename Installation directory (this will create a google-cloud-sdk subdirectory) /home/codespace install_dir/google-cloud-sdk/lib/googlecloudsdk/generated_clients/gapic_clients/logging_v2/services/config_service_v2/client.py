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
from typing import Dict, Mapping, MutableMapping, MutableSequence, Optional, Sequence, Tuple, Type, Union, cast

from googlecloudsdk.generated_clients.gapic_clients.logging_v2 import gapic_version as package_version

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

from google.api_core import operation  # type: ignore
from google.api_core import operation_async  # type: ignore
from cloudsdk.google.protobuf import empty_pb2  # type: ignore
from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2 import pagers
from googlecloudsdk.generated_clients.gapic_clients.logging_v2.types import logging_config
from .transports.base import ConfigServiceV2Transport, DEFAULT_CLIENT_INFO
from .transports.grpc import ConfigServiceV2GrpcTransport
from .transports.grpc_asyncio import ConfigServiceV2GrpcAsyncIOTransport
from .transports.rest import ConfigServiceV2RestTransport


class ConfigServiceV2ClientMeta(type):
    """Metaclass for the ConfigServiceV2 client.

    This provides class-level methods for building and retrieving
    support objects (e.g. transport) without polluting the client instance
    objects.
    """
    _transport_registry = OrderedDict()  # type: Dict[str, Type[ConfigServiceV2Transport]]
    _transport_registry["grpc"] = ConfigServiceV2GrpcTransport
    _transport_registry["grpc_asyncio"] = ConfigServiceV2GrpcAsyncIOTransport
    _transport_registry["rest"] = ConfigServiceV2RestTransport

    def get_transport_class(cls,
            label: Optional[str] = None,
        ) -> Type[ConfigServiceV2Transport]:
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


class ConfigServiceV2Client(metaclass=ConfigServiceV2ClientMeta):
    """Service for configuring sinks used to route log entries."""

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

    DEFAULT_ENDPOINT = "logging.googleapis.com"
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
            ConfigServiceV2Client: The constructed client.
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
            ConfigServiceV2Client: The constructed client.
        """
        credentials = service_account.Credentials.from_service_account_file(
            filename)
        kwargs["credentials"] = credentials
        return cls(*args, **kwargs)

    from_service_account_json = from_service_account_file

    @property
    def transport(self) -> ConfigServiceV2Transport:
        """Returns the transport used by the client instance.

        Returns:
            ConfigServiceV2Transport: The transport used by the client
                instance.
        """
        return self._transport

    @staticmethod
    def cmek_settings_path(project: str,) -> str:
        """Returns a fully-qualified cmek_settings string."""
        return "projects/{project}/cmekSettings".format(project=project, )

    @staticmethod
    def parse_cmek_settings_path(path: str) -> Dict[str,str]:
        """Parses a cmek_settings path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/cmekSettings$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def link_path(project: str,location: str,bucket: str,link: str,) -> str:
        """Returns a fully-qualified link string."""
        return "projects/{project}/locations/{location}/buckets/{bucket}/links/{link}".format(project=project, location=location, bucket=bucket, link=link, )

    @staticmethod
    def parse_link_path(path: str) -> Dict[str,str]:
        """Parses a link path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/locations/(?P<location>.+?)/buckets/(?P<bucket>.+?)/links/(?P<link>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def log_bucket_path(project: str,location: str,bucket: str,) -> str:
        """Returns a fully-qualified log_bucket string."""
        return "projects/{project}/locations/{location}/buckets/{bucket}".format(project=project, location=location, bucket=bucket, )

    @staticmethod
    def parse_log_bucket_path(path: str) -> Dict[str,str]:
        """Parses a log_bucket path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/locations/(?P<location>.+?)/buckets/(?P<bucket>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def log_exclusion_path(project: str,exclusion: str,) -> str:
        """Returns a fully-qualified log_exclusion string."""
        return "projects/{project}/exclusions/{exclusion}".format(project=project, exclusion=exclusion, )

    @staticmethod
    def parse_log_exclusion_path(path: str) -> Dict[str,str]:
        """Parses a log_exclusion path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/exclusions/(?P<exclusion>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def log_sink_path(project: str,sink: str,) -> str:
        """Returns a fully-qualified log_sink string."""
        return "projects/{project}/sinks/{sink}".format(project=project, sink=sink, )

    @staticmethod
    def parse_log_sink_path(path: str) -> Dict[str,str]:
        """Parses a log_sink path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/sinks/(?P<sink>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def log_view_path(project: str,location: str,bucket: str,view: str,) -> str:
        """Returns a fully-qualified log_view string."""
        return "projects/{project}/locations/{location}/buckets/{bucket}/views/{view}".format(project=project, location=location, bucket=bucket, view=view, )

    @staticmethod
    def parse_log_view_path(path: str) -> Dict[str,str]:
        """Parses a log_view path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/locations/(?P<location>.+?)/buckets/(?P<bucket>.+?)/views/(?P<view>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def recent_query_path(project: str,location: str,recent_query: str,) -> str:
        """Returns a fully-qualified recent_query string."""
        return "projects/{project}/locations/{location}/recentQueries/{recent_query}".format(project=project, location=location, recent_query=recent_query, )

    @staticmethod
    def parse_recent_query_path(path: str) -> Dict[str,str]:
        """Parses a recent_query path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/locations/(?P<location>.+?)/recentQueries/(?P<recent_query>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def saved_query_path(project: str,location: str,saved_query: str,) -> str:
        """Returns a fully-qualified saved_query string."""
        return "projects/{project}/locations/{location}/savedQueries/{saved_query}".format(project=project, location=location, saved_query=saved_query, )

    @staticmethod
    def parse_saved_query_path(path: str) -> Dict[str,str]:
        """Parses a saved_query path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/locations/(?P<location>.+?)/savedQueries/(?P<saved_query>.+?)$", path)
        return m.groupdict() if m else {}

    @staticmethod
    def settings_path(project: str,) -> str:
        """Returns a fully-qualified settings string."""
        return "projects/{project}/settings".format(project=project, )

    @staticmethod
    def parse_settings_path(path: str) -> Dict[str,str]:
        """Parses a settings path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/settings$", path)
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
            transport: Optional[Union[str, ConfigServiceV2Transport]] = None,
            client_options: Optional[Union[client_options_lib.ClientOptions, dict]] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            ) -> None:
        """Instantiates the config service v2 client.

        Args:
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
            transport (Union[str, ConfigServiceV2Transport]): The
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
        if isinstance(transport, ConfigServiceV2Transport):
            # transport is a ConfigServiceV2Transport instance.
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

    def list_buckets(self,
            request: Optional[Union[logging_config.ListBucketsRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListBucketsPager:
        r"""Lists log buckets.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_list_buckets():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.ListBucketsRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_buckets(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListBucketsRequest, dict]):
                The request object. The parameters to ``ListBuckets``.
            parent (str):
                Required. The parent resource whose buckets are to be
                listed:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]"

                Note: The locations portion of the resource must be
                specified, but supplying the character ``-`` in place of
                [LOCATION_ID] will return all buckets.

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListBucketsPager:
                The response from ListBuckets.

                Iterating over this object will yield
                results and resolve additional pages
                automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.ListBucketsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.ListBucketsRequest):
            request = logging_config.ListBucketsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_buckets]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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
        response = pagers.ListBucketsPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def get_bucket(self,
            request: Optional[Union[logging_config.GetBucketRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogBucket:
        r"""Gets a log bucket.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_get_bucket():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.GetBucketRequest(
                    name="name_value",
                )

                # Make the request
                response = client.get_bucket(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetBucketRequest, dict]):
                The request object. The parameters to ``GetBucket``.
            name (str):
                Required. The resource name of the bucket:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

                For example:

                ``"projects/my-project/locations/global/buckets/my-bucket"``

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket:
                Describes a repository in which log
                entries are stored.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.GetBucketRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.GetBucketRequest):
            request = logging_config.GetBucketRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.get_bucket]

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

    def create_bucket_async(self,
            request: Optional[Union[logging_config.CreateBucketRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            bucket: Optional[logging_config.LogBucket] = None,
            bucket_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> operation.Operation:
        r"""Creates a log bucket asynchronously that can be used
        to store log entries.
        After a bucket has been created, the bucket's location
        cannot be changed.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_create_bucket_async():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.CreateBucketRequest(
                    parent="parent_value",
                    bucket_id="bucket_id_value",
                )

                # Make the request
                operation = client.create_bucket_async(request=request)

                print("Waiting for operation to complete...")

                response = operation.result()

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateBucketRequest, dict]):
                The request object. The parameters to ``CreateBucket``.
            parent (str):
                Required. The resource in which to create the log
                bucket:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]"

                For example:

                ``"projects/my-project/locations/global"``

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket):
                Required. The new bucket. The region
                specified in the new bucket must be
                compliant with any Location Restriction
                Org Policy. The name field in the bucket
                is ignored.

                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket_id (str):
                Required. A client-assigned identifier such as
                ``"my-bucket"``. Identifiers are limited to 100
                characters and can include only letters, digits,
                underscores, hyphens, and periods. Bucket identifiers
                must start with an alphanumeric character.

                This corresponds to the ``bucket_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.api_core.operation.Operation:
                An object representing a long-running operation.

                The result type for the operation will be
                :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket`
                Describes a repository in which log entries are stored.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent, bucket, bucket_id])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.CreateBucketRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.CreateBucketRequest):
            request = logging_config.CreateBucketRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent
            if bucket is not None:
                request.bucket = bucket
            if bucket_id is not None:
                request.bucket_id = bucket_id

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.create_bucket_async]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Wrap the response in an operation future.
        response = operation.from_gapic(
            response,
            self._transport.operations_client,
            logging_config.LogBucket,
            metadata_type=logging_config.BucketMetadata,
        )

        # Done; return the response.
        return response

    def update_bucket_async(self,
            request: Optional[Union[logging_config.UpdateBucketRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            bucket: Optional[logging_config.LogBucket] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> operation.Operation:
        r"""Updates a log bucket asynchronously.

        If the bucket has a ``lifecycle_state`` of ``DELETE_REQUESTED``,
        then ``FAILED_PRECONDITION`` will be returned.

        After a bucket has been created, the bucket's location cannot be
        changed.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_update_bucket_async():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.UpdateBucketRequest(
                    name="name_value",
                )

                # Make the request
                operation = client.update_bucket_async(request=request)

                print("Waiting for operation to complete...")

                response = operation.result()

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateBucketRequest, dict]):
                The request object. The parameters to ``UpdateBucket``.
            name (str):
                Required. The full resource name of the bucket to
                update.

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

                For example:

                ``"projects/my-project/locations/global/buckets/my-bucket"``

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket):
                Required. The updated bucket.
                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (google.protobuf.field_mask_pb2.FieldMask):
                Required. Field mask that specifies the fields in
                ``bucket`` that need an update. A bucket field will be
                overwritten if, and only if, it is in the update mask.
                ``name`` and output only fields cannot be updated.

                For a detailed ``FieldMask`` definition, see:
                https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#google.protobuf.FieldMask

                For example: ``updateMask=retention_days``

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.api_core.operation.Operation:
                An object representing a long-running operation.

                The result type for the operation will be
                :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket`
                Describes a repository in which log entries are stored.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name, bucket, update_mask])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.UpdateBucketRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.UpdateBucketRequest):
            request = logging_config.UpdateBucketRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name
            if bucket is not None:
                request.bucket = bucket
            if update_mask is not None:
                request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.update_bucket_async]

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

        # Wrap the response in an operation future.
        response = operation.from_gapic(
            response,
            self._transport.operations_client,
            logging_config.LogBucket,
            metadata_type=logging_config.BucketMetadata,
        )

        # Done; return the response.
        return response

    def create_bucket(self,
            request: Optional[Union[logging_config.CreateBucketRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            bucket: Optional[logging_config.LogBucket] = None,
            bucket_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogBucket:
        r"""Creates a log bucket that can be used to store log
        entries. After a bucket has been created, the bucket's
        location cannot be changed.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_create_bucket():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.CreateBucketRequest(
                    parent="parent_value",
                    bucket_id="bucket_id_value",
                )

                # Make the request
                response = client.create_bucket(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateBucketRequest, dict]):
                The request object. The parameters to ``CreateBucket``.
            parent (str):
                Required. The resource in which to create the log
                bucket:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]"

                For example:

                ``"projects/my-project/locations/global"``

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket):
                Required. The new bucket. The region
                specified in the new bucket must be
                compliant with any Location Restriction
                Org Policy. The name field in the bucket
                is ignored.

                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket_id (str):
                Required. A client-assigned identifier such as
                ``"my-bucket"``. Identifiers are limited to 100
                characters and can include only letters, digits,
                underscores, hyphens, and periods. Bucket identifiers
                must start with an alphanumeric character.

                This corresponds to the ``bucket_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket:
                Describes a repository in which log
                entries are stored.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent, bucket, bucket_id])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.CreateBucketRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.CreateBucketRequest):
            request = logging_config.CreateBucketRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent
            if bucket is not None:
                request.bucket = bucket
            if bucket_id is not None:
                request.bucket_id = bucket_id

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.create_bucket]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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

    def update_bucket(self,
            request: Optional[Union[logging_config.UpdateBucketRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            bucket: Optional[logging_config.LogBucket] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogBucket:
        r"""Updates a log bucket.

        If the bucket has a ``lifecycle_state`` of ``DELETE_REQUESTED``,
        then ``FAILED_PRECONDITION`` will be returned.

        After a bucket has been created, the bucket's location cannot be
        changed.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_update_bucket():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.UpdateBucketRequest(
                    name="name_value",
                )

                # Make the request
                response = client.update_bucket(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateBucketRequest, dict]):
                The request object. The parameters to ``UpdateBucket``.
            name (str):
                Required. The full resource name of the bucket to
                update.

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

                For example:

                ``"projects/my-project/locations/global/buckets/my-bucket"``

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket):
                Required. The updated bucket.
                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (google.protobuf.field_mask_pb2.FieldMask):
                Required. Field mask that specifies the fields in
                ``bucket`` that need an update. A bucket field will be
                overwritten if, and only if, it is in the update mask.
                ``name`` and output only fields cannot be updated.

                For a detailed ``FieldMask`` definition, see:
                https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#google.protobuf.FieldMask

                For example: ``updateMask=retention_days``

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket:
                Describes a repository in which log
                entries are stored.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name, bucket, update_mask])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.UpdateBucketRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.UpdateBucketRequest):
            request = logging_config.UpdateBucketRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name
            if bucket is not None:
                request.bucket = bucket
            if update_mask is not None:
                request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.update_bucket]

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

    def delete_bucket(self,
            request: Optional[Union[logging_config.DeleteBucketRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Deletes a log bucket.

        Changes the bucket's ``lifecycle_state`` to the
        ``DELETE_REQUESTED`` state. After 7 days, the bucket will be
        purged and all log entries in the bucket will be permanently
        deleted.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_delete_bucket():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.DeleteBucketRequest(
                    name="name_value",
                )

                # Make the request
                client.delete_bucket(request=request)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteBucketRequest, dict]):
                The request object. The parameters to ``DeleteBucket``.
            name (str):
                Required. The full resource name of the bucket to
                delete.

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

                For example:

                ``"projects/my-project/locations/global/buckets/my-bucket"``

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
        # in a logging_config.DeleteBucketRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.DeleteBucketRequest):
            request = logging_config.DeleteBucketRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.delete_bucket]

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

    def undelete_bucket(self,
            request: Optional[Union[logging_config.UndeleteBucketRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Undeletes a log bucket. A bucket that has been
        deleted can be undeleted within the grace period of 7
        days.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_undelete_bucket():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.UndeleteBucketRequest(
                    name="name_value",
                )

                # Make the request
                client.undelete_bucket(request=request)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UndeleteBucketRequest, dict]):
                The request object. The parameters to ``UndeleteBucket``.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.UndeleteBucketRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.UndeleteBucketRequest):
            request = logging_config.UndeleteBucketRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.undelete_bucket]

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

    def list_views(self,
            request: Optional[Union[logging_config.ListViewsRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListViewsPager:
        r"""Lists views on a log bucket.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_list_views():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.ListViewsRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_views(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListViewsRequest, dict]):
                The request object. The parameters to ``ListViews``.
            parent (str):
                Required. The bucket whose views are to be listed:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListViewsPager:
                The response from ListViews.

                Iterating over this object will yield
                results and resolve additional pages
                automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.ListViewsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.ListViewsRequest):
            request = logging_config.ListViewsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_views]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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
        response = pagers.ListViewsPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def get_view(self,
            request: Optional[Union[logging_config.GetViewRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogView:
        r"""Gets a view on a log bucket.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_get_view():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.GetViewRequest(
                    name="name_value",
                )

                # Make the request
                response = client.get_view(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetViewRequest, dict]):
                The request object. The parameters to ``GetView``.
            name (str):
                Required. The resource name of the policy:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]"

                For example:

                ``"projects/my-project/locations/global/buckets/my-bucket/views/my-view"``

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogView:
                Describes a view over log entries in
                a bucket.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.GetViewRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.GetViewRequest):
            request = logging_config.GetViewRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.get_view]

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

    def create_view(self,
            request: Optional[Union[logging_config.CreateViewRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            view: Optional[logging_config.LogView] = None,
            view_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogView:
        r"""Creates a view over log entries in a log bucket. A
        bucket may contain a maximum of 30 views.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_create_view():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.CreateViewRequest(
                    parent="parent_value",
                    view_id="view_id_value",
                )

                # Make the request
                response = client.create_view(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateViewRequest, dict]):
                The request object. The parameters to ``CreateView``.
            parent (str):
                Required. The bucket in which to create the view

                ::

                    `"projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"`

                For example:

                ``"projects/my-project/locations/global/buckets/my-bucket"``

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            view (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogView):
                Required. The new view.
                This corresponds to the ``view`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            view_id (str):
                Required. A client-assigned identifier such as
                ``"my-view"``. Identifiers are limited to 100 characters
                and can include only letters, digits, underscores,
                hyphens, and periods.

                This corresponds to the ``view_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogView:
                Describes a view over log entries in
                a bucket.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent, view, view_id])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.CreateViewRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.CreateViewRequest):
            request = logging_config.CreateViewRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent
            if view is not None:
                request.view = view
            if view_id is not None:
                request.view_id = view_id

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.create_view]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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

    def update_view(self,
            request: Optional[Union[logging_config.UpdateViewRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogView:
        r"""Updates a view on a log bucket. This method replaces the value
        of the ``filter`` field from the existing view with the
        corresponding value from the new view. If an ``UNAVAILABLE``
        error is returned, this indicates that system is not in a state
        where it can update the view. If this occurs, please try again
        in a few minutes.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_update_view():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.UpdateViewRequest(
                    name="name_value",
                )

                # Make the request
                response = client.update_view(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateViewRequest, dict]):
                The request object. The parameters to ``UpdateView``.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogView:
                Describes a view over log entries in
                a bucket.

        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.UpdateViewRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.UpdateViewRequest):
            request = logging_config.UpdateViewRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.update_view]

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

    def delete_view(self,
            request: Optional[Union[logging_config.DeleteViewRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Deletes a view on a log bucket. If an ``UNAVAILABLE`` error is
        returned, this indicates that system is not in a state where it
        can delete the view. If this occurs, please try again in a few
        minutes.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_delete_view():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.DeleteViewRequest(
                    name="name_value",
                )

                # Make the request
                client.delete_view(request=request)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteViewRequest, dict]):
                The request object. The parameters to ``DeleteView``.
            name (str):
                Required. The full resource name of the view to delete:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]"

                For example:

                ::

                   `"projects/my-project/locations/global/buckets/my-bucket/views/my-view"`

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
        # in a logging_config.DeleteViewRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.DeleteViewRequest):
            request = logging_config.DeleteViewRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.delete_view]

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

    def list_exclusions(self,
            request: Optional[Union[logging_config.ListExclusionsRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListExclusionsPager:
        r"""Lists all the exclusions on the \_Default sink in a parent
        resource.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_list_exclusions():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.ListExclusionsRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_exclusions(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListExclusionsRequest, dict]):
                The request object. The parameters to ``ListExclusions``.
            parent (str):
                Required. The parent resource whose exclusions are to be
                listed.

                ::

                    "projects/[PROJECT_ID]"
                    "organizations/[ORGANIZATION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]"
                    "folders/[FOLDER_ID]"

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListExclusionsPager:
                Result returned from ListExclusions.

                Iterating over this object will yield results and
                resolve additional pages automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.ListExclusionsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.ListExclusionsRequest):
            request = logging_config.ListExclusionsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_exclusions]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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
        response = pagers.ListExclusionsPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def get_exclusion(self,
            request: Optional[Union[logging_config.GetExclusionRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogExclusion:
        r"""Gets the description of an exclusion in the \_Default sink.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_get_exclusion():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.GetExclusionRequest(
                    name="name_value",
                )

                # Make the request
                response = client.get_exclusion(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetExclusionRequest, dict]):
                The request object. The parameters to ``GetExclusion``.
            name (str):
                Required. The resource name of an existing exclusion:

                ::

                    "projects/[PROJECT_ID]/exclusions/[EXCLUSION_ID]"
                    "organizations/[ORGANIZATION_ID]/exclusions/[EXCLUSION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/exclusions/[EXCLUSION_ID]"
                    "folders/[FOLDER_ID]/exclusions/[EXCLUSION_ID]"

                For example:

                ``"projects/my-project/exclusions/my-exclusion"``

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion:
                Specifies a set of log entries that are filtered out by a sink. If
                   your Google Cloud resource receives a large volume of
                   log entries, you can use exclusions to reduce your
                   chargeable logs. Note that exclusions on
                   organization-level and folder-level sinks don't apply
                   to child resources. Note also that you cannot modify
                   the \_Required sink or exclude logs from it.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.GetExclusionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.GetExclusionRequest):
            request = logging_config.GetExclusionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.get_exclusion]

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

    def create_exclusion(self,
            request: Optional[Union[logging_config.CreateExclusionRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            exclusion: Optional[logging_config.LogExclusion] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogExclusion:
        r"""Creates a new exclusion in the \_Default sink in a specified
        parent resource. Only log entries belonging to that resource can
        be excluded. You can have up to 10 exclusions in a resource.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_create_exclusion():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                exclusion = logging_v2.LogExclusion()
                exclusion.filter = "filter_value"

                request = logging_v2.CreateExclusionRequest(
                    parent="parent_value",
                    exclusion=exclusion,
                )

                # Make the request
                response = client.create_exclusion(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateExclusionRequest, dict]):
                The request object. The parameters to ``CreateExclusion``.
            parent (str):
                Required. The parent resource in which to create the
                exclusion:

                ::

                    "projects/[PROJECT_ID]"
                    "organizations/[ORGANIZATION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]"
                    "folders/[FOLDER_ID]"

                For examples:

                ``"projects/my-logging-project"``
                ``"organizations/123456789"``

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            exclusion (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion):
                Required. The new exclusion, whose ``name`` parameter is
                an exclusion name that is not already used in the parent
                resource.

                This corresponds to the ``exclusion`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion:
                Specifies a set of log entries that are filtered out by a sink. If
                   your Google Cloud resource receives a large volume of
                   log entries, you can use exclusions to reduce your
                   chargeable logs. Note that exclusions on
                   organization-level and folder-level sinks don't apply
                   to child resources. Note also that you cannot modify
                   the \_Required sink or exclude logs from it.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent, exclusion])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.CreateExclusionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.CreateExclusionRequest):
            request = logging_config.CreateExclusionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent
            if exclusion is not None:
                request.exclusion = exclusion

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.create_exclusion]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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

    def update_exclusion(self,
            request: Optional[Union[logging_config.UpdateExclusionRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            exclusion: Optional[logging_config.LogExclusion] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogExclusion:
        r"""Changes one or more properties of an existing exclusion in the
        \_Default sink.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_update_exclusion():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                exclusion = logging_v2.LogExclusion()
                exclusion.filter = "filter_value"

                request = logging_v2.UpdateExclusionRequest(
                    name="name_value",
                    exclusion=exclusion,
                )

                # Make the request
                response = client.update_exclusion(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateExclusionRequest, dict]):
                The request object. The parameters to ``UpdateExclusion``.
            name (str):
                Required. The resource name of the exclusion to update:

                ::

                    "projects/[PROJECT_ID]/exclusions/[EXCLUSION_ID]"
                    "organizations/[ORGANIZATION_ID]/exclusions/[EXCLUSION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/exclusions/[EXCLUSION_ID]"
                    "folders/[FOLDER_ID]/exclusions/[EXCLUSION_ID]"

                For example:

                ``"projects/my-project/exclusions/my-exclusion"``

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            exclusion (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion):
                Required. New values for the existing exclusion. Only
                the fields specified in ``update_mask`` are relevant.

                This corresponds to the ``exclusion`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (google.protobuf.field_mask_pb2.FieldMask):
                Required. A non-empty list of fields to change in the
                existing exclusion. New values for the fields are taken
                from the corresponding fields in the
                [LogExclusion][google.logging.v2.LogExclusion] included
                in this request. Fields not mentioned in ``update_mask``
                are not changed and are ignored in the request.

                For example, to change the filter and description of an
                exclusion, specify an ``update_mask`` of
                ``"filter,description"``.

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion:
                Specifies a set of log entries that are filtered out by a sink. If
                   your Google Cloud resource receives a large volume of
                   log entries, you can use exclusions to reduce your
                   chargeable logs. Note that exclusions on
                   organization-level and folder-level sinks don't apply
                   to child resources. Note also that you cannot modify
                   the \_Required sink or exclude logs from it.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name, exclusion, update_mask])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.UpdateExclusionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.UpdateExclusionRequest):
            request = logging_config.UpdateExclusionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name
            if exclusion is not None:
                request.exclusion = exclusion
            if update_mask is not None:
                request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.update_exclusion]

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

    def delete_exclusion(self,
            request: Optional[Union[logging_config.DeleteExclusionRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Deletes an exclusion in the \_Default sink.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_delete_exclusion():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.DeleteExclusionRequest(
                    name="name_value",
                )

                # Make the request
                client.delete_exclusion(request=request)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteExclusionRequest, dict]):
                The request object. The parameters to ``DeleteExclusion``.
            name (str):
                Required. The resource name of an existing exclusion to
                delete:

                ::

                    "projects/[PROJECT_ID]/exclusions/[EXCLUSION_ID]"
                    "organizations/[ORGANIZATION_ID]/exclusions/[EXCLUSION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/exclusions/[EXCLUSION_ID]"
                    "folders/[FOLDER_ID]/exclusions/[EXCLUSION_ID]"

                For example:

                ``"projects/my-project/exclusions/my-exclusion"``

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
        # in a logging_config.DeleteExclusionRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.DeleteExclusionRequest):
            request = logging_config.DeleteExclusionRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.delete_exclusion]

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

    def list_sinks(self,
            request: Optional[Union[logging_config.ListSinksRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListSinksPager:
        r"""Lists sinks.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_list_sinks():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.ListSinksRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_sinks(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSinksRequest, dict]):
                The request object. The parameters to ``ListSinks``.
            parent (str):
                Required. The parent resource whose sinks are to be
                listed:

                ::

                    "projects/[PROJECT_ID]"
                    "organizations/[ORGANIZATION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]"
                    "folders/[FOLDER_ID]"

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListSinksPager:
                Result returned from ListSinks.

                Iterating over this object will yield results and
                resolve additional pages automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.ListSinksRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.ListSinksRequest):
            request = logging_config.ListSinksRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_sinks]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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
        response = pagers.ListSinksPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def get_sink(self,
            request: Optional[Union[logging_config.GetSinkRequest, dict]] = None,
            *,
            sink_name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogSink:
        r"""Gets a sink.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_get_sink():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.GetSinkRequest(
                    sink_name="sink_name_value",
                )

                # Make the request
                response = client.get_sink(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetSinkRequest, dict]):
                The request object. The parameters to ``GetSink``.
            sink_name (str):
                Required. The resource name of the sink:

                ::

                    "projects/[PROJECT_ID]/sinks/[SINK_ID]"
                    "organizations/[ORGANIZATION_ID]/sinks/[SINK_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/sinks/[SINK_ID]"
                    "folders/[FOLDER_ID]/sinks/[SINK_ID]"

                For example:

                ``"projects/my-project/sinks/my-sink"``

                This corresponds to the ``sink_name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink:
                Describes a sink used to export log entries to one of the following
                   destinations:

                   -  a Cloud Logging log bucket,
                   -  a Cloud Storage bucket,
                   -  a BigQuery dataset,
                   -  a Pub/Sub topic,
                   -  a Cloud project.

                   A logs filter controls which log entries are
                   exported. The sink must be created within a project,
                   organization, billing account, or folder.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([sink_name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.GetSinkRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.GetSinkRequest):
            request = logging_config.GetSinkRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if sink_name is not None:
                request.sink_name = sink_name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.get_sink]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("sink_name", request.sink_name),
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

    def create_sink(self,
            request: Optional[Union[logging_config.CreateSinkRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            sink: Optional[logging_config.LogSink] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogSink:
        r"""Creates a sink that exports specified log entries to a
        destination. The export begins upon ingress, unless the sink's
        ``writer_identity`` is not permitted to write to the
        destination. A sink can export log entries only from the
        resource owning the sink.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_create_sink():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                sink = logging_v2.LogSink()
                sink.destination = "destination_value"

                request = logging_v2.CreateSinkRequest(
                    parent="parent_value",
                    sink=sink,
                )

                # Make the request
                response = client.create_sink(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateSinkRequest, dict]):
                The request object. The parameters to ``CreateSink``.
            parent (str):
                Required. The resource in which to create the sink:

                ::

                    "projects/[PROJECT_ID]"
                    "organizations/[ORGANIZATION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]"
                    "folders/[FOLDER_ID]"

                For examples:

                ``"projects/my-project"`` ``"organizations/123456789"``

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            sink (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink):
                Required. The new sink, whose ``name`` parameter is a
                sink identifier that is not already in use.

                This corresponds to the ``sink`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink:
                Describes a sink used to export log entries to one of the following
                   destinations:

                   -  a Cloud Logging log bucket,
                   -  a Cloud Storage bucket,
                   -  a BigQuery dataset,
                   -  a Pub/Sub topic,
                   -  a Cloud project.

                   A logs filter controls which log entries are
                   exported. The sink must be created within a project,
                   organization, billing account, or folder.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent, sink])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.CreateSinkRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.CreateSinkRequest):
            request = logging_config.CreateSinkRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent
            if sink is not None:
                request.sink = sink

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.create_sink]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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

    def update_sink(self,
            request: Optional[Union[logging_config.UpdateSinkRequest, dict]] = None,
            *,
            sink_name: Optional[str] = None,
            sink: Optional[logging_config.LogSink] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.LogSink:
        r"""Updates a sink. This method replaces the values of the
        ``destination`` and ``filter`` fields of the existing sink with
        the corresponding values from the new sink.

        The updated sink might also have a new ``writer_identity``; see
        the ``unique_writer_identity`` field.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_update_sink():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                sink = logging_v2.LogSink()
                sink.destination = "destination_value"

                request = logging_v2.UpdateSinkRequest(
                    sink_name="sink_name_value",
                    sink=sink,
                )

                # Make the request
                response = client.update_sink(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateSinkRequest, dict]):
                The request object. The parameters to ``UpdateSink``.
            sink_name (str):
                Required. The full resource name of the sink to update,
                including the parent resource and the sink identifier:

                ::

                    "projects/[PROJECT_ID]/sinks/[SINK_ID]"
                    "organizations/[ORGANIZATION_ID]/sinks/[SINK_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/sinks/[SINK_ID]"
                    "folders/[FOLDER_ID]/sinks/[SINK_ID]"

                For example:

                ``"projects/my-project/sinks/my-sink"``

                This corresponds to the ``sink_name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            sink (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink):
                Required. The updated sink, whose name is the same
                identifier that appears as part of ``sink_name``.

                This corresponds to the ``sink`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (google.protobuf.field_mask_pb2.FieldMask):
                Optional. Field mask that specifies the fields in
                ``sink`` that need an update. A sink field will be
                overwritten if, and only if, it is in the update mask.
                ``name`` and output only fields cannot be updated.

                An empty ``updateMask`` is temporarily treated as using
                the following mask for backwards compatibility purposes:

                ``destination,filter,includeChildren``

                At some point in the future, behavior will be removed
                and specifying an empty ``updateMask`` will be an error.

                For a detailed ``FieldMask`` definition, see
                https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#google.protobuf.FieldMask

                For example: ``updateMask=filter``

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink:
                Describes a sink used to export log entries to one of the following
                   destinations:

                   -  a Cloud Logging log bucket,
                   -  a Cloud Storage bucket,
                   -  a BigQuery dataset,
                   -  a Pub/Sub topic,
                   -  a Cloud project.

                   A logs filter controls which log entries are
                   exported. The sink must be created within a project,
                   organization, billing account, or folder.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([sink_name, sink, update_mask])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.UpdateSinkRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.UpdateSinkRequest):
            request = logging_config.UpdateSinkRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if sink_name is not None:
                request.sink_name = sink_name
            if sink is not None:
                request.sink = sink
            if update_mask is not None:
                request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.update_sink]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("sink_name", request.sink_name),
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

    def delete_sink(self,
            request: Optional[Union[logging_config.DeleteSinkRequest, dict]] = None,
            *,
            sink_name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Deletes a sink. If the sink has a unique ``writer_identity``,
        then that service account is also deleted.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_delete_sink():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.DeleteSinkRequest(
                    sink_name="sink_name_value",
                )

                # Make the request
                client.delete_sink(request=request)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteSinkRequest, dict]):
                The request object. The parameters to ``DeleteSink``.
            sink_name (str):
                Required. The full resource name of the sink to delete,
                including the parent resource and the sink identifier:

                ::

                    "projects/[PROJECT_ID]/sinks/[SINK_ID]"
                    "organizations/[ORGANIZATION_ID]/sinks/[SINK_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/sinks/[SINK_ID]"
                    "folders/[FOLDER_ID]/sinks/[SINK_ID]"

                For example:

                ``"projects/my-project/sinks/my-sink"``

                This corresponds to the ``sink_name`` field
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
        has_flattened_params = any([sink_name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.DeleteSinkRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.DeleteSinkRequest):
            request = logging_config.DeleteSinkRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if sink_name is not None:
                request.sink_name = sink_name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.delete_sink]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("sink_name", request.sink_name),
            )),
        )

        # Send the request.
        rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    def list_links(self,
            request: Optional[Union[logging_config.ListLinksRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListLinksPager:
        r"""Lists links.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_list_links():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.ListLinksRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_links(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLinksRequest, dict]):
                The request object. The parameters to ListLinks.
            parent (str):
                Required. The parent resource whose links are to be
                listed:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListLinksPager:
                The response from ListLinks.

                Iterating over this object will yield
                results and resolve additional pages
                automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.ListLinksRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.ListLinksRequest):
            request = logging_config.ListLinksRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_links]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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
        response = pagers.ListLinksPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def get_link(self,
            request: Optional[Union[logging_config.GetLinkRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.Link:
        r"""Gets a link.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_get_link():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.GetLinkRequest(
                    name="name_value",
                )

                # Make the request
                response = client.get_link(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetLinkRequest, dict]):
                The request object. The parameters to GetLink.
            name (str):
                Required. The resource name of the link:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Link:
                Describes a link connected to an
                analytics enabled bucket.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.GetLinkRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.GetLinkRequest):
            request = logging_config.GetLinkRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.get_link]

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

    def create_link(self,
            request: Optional[Union[logging_config.CreateLinkRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            link: Optional[logging_config.Link] = None,
            link_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> operation.Operation:
        r"""Asynchronously creates a linked dataset in BigQuery
        which makes it possible to use BigQuery to read the logs
        stored in the log bucket. A log bucket may currently
        only contain one link.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_create_link():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.CreateLinkRequest(
                    parent="parent_value",
                    link_id="link_id_value",
                )

                # Make the request
                operation = client.create_link(request=request)

                print("Waiting for operation to complete...")

                response = operation.result()

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateLinkRequest, dict]):
                The request object. The parameters to CreateLink.
            parent (str):
                Required. The full resource name of the bucket to create
                a link for.

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            link (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Link):
                Required. The new link.
                This corresponds to the ``link`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            link_id (str):
                Required. The ID to use for the link. The link_id can
                have up to 100 characters. A valid link_id must only
                have alphanumeric characters and underscores within it.

                This corresponds to the ``link_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.api_core.operation.Operation:
                An object representing a long-running operation.

                The result type for the operation will be
                :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Link`
                Describes a link connected to an analytics enabled
                bucket.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent, link, link_id])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.CreateLinkRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.CreateLinkRequest):
            request = logging_config.CreateLinkRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent
            if link is not None:
                request.link = link
            if link_id is not None:
                request.link_id = link_id

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.create_link]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
        )

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Wrap the response in an operation future.
        response = operation.from_gapic(
            response,
            self._transport.operations_client,
            logging_config.Link,
            metadata_type=logging_config.LinkMetadata,
        )

        # Done; return the response.
        return response

    def delete_link(self,
            request: Optional[Union[logging_config.DeleteLinkRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> operation.Operation:
        r"""Deletes a link. This will also delete the
        corresponding BigQuery linked dataset.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_delete_link():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.DeleteLinkRequest(
                    name="name_value",
                )

                # Make the request
                operation = client.delete_link(request=request)

                print("Waiting for operation to complete...")

                response = operation.result()

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteLinkRequest, dict]):
                The request object. The parameters to DeleteLink.
            name (str):
                Required. The full resource name of the link to delete.

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.api_core.operation.Operation:
                An object representing a long-running operation.

                The result type for the operation will be :class:`google.protobuf.empty_pb2.Empty` A generic empty message that you can re-use to avoid defining duplicated
                   empty messages in your APIs. A typical example is to
                   use it as the request or the response type of an API
                   method. For instance:

                      service Foo {
                         rpc Bar(google.protobuf.Empty) returns
                         (google.protobuf.Empty);

                      }

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.DeleteLinkRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.DeleteLinkRequest):
            request = logging_config.DeleteLinkRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.delete_link]

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

        # Wrap the response in an operation future.
        response = operation.from_gapic(
            response,
            self._transport.operations_client,
            empty_pb2.Empty,
            metadata_type=logging_config.LinkMetadata,
        )

        # Done; return the response.
        return response

    def get_cmek_settings(self,
            request: Optional[Union[logging_config.GetCmekSettingsRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.CmekSettings:
        r"""Gets the Logging CMEK settings for the given resource.

        Note: CMEK for the Log Router can be configured for Google Cloud
        projects, folders, organizations, and billing accounts. Once
        configured for an organization, it applies to all projects and
        folders in the Google Cloud organization.

        See `Enabling CMEK for Log
        Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
        for more information.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_get_cmek_settings():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.GetCmekSettingsRequest(
                    name="name_value",
                )

                # Make the request
                response = client.get_cmek_settings(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetCmekSettingsRequest, dict]):
                The request object. The parameters to
                [GetCmekSettings][google.logging.v2.ConfigServiceV2.GetCmekSettings].

                See `Enabling CMEK for Log
                Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.
            name (str):
                Required. The resource for which to retrieve CMEK
                settings.

                ::

                    "projects/[PROJECT_ID]/cmekSettings"
                    "organizations/[ORGANIZATION_ID]/cmekSettings"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/cmekSettings"
                    "folders/[FOLDER_ID]/cmekSettings"

                For example:

                ``"organizations/12345/cmekSettings"``

                Note: CMEK for the Log Router can be configured for
                Google Cloud projects, folders, organizations, and
                billing accounts. Once configured for an organization,
                it applies to all projects and folders in the Google
                Cloud organization.

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CmekSettings:
                Describes the customer-managed encryption key (CMEK) settings associated with
                   a project, folder, organization, billing account, or
                   flexible resource.

                   Note: CMEK for the Log Router can currently only be
                   configured for Google Cloud organizations. Once
                   configured, it applies to all projects and folders in
                   the Google Cloud organization.

                   See [Enabling CMEK for Log
                   Router](\ https://cloud.google.com/logging/docs/routing/managed-encryption)
                   for more information.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.GetCmekSettingsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.GetCmekSettingsRequest):
            request = logging_config.GetCmekSettingsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.get_cmek_settings]

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

    def update_cmek_settings(self,
            request: Optional[Union[logging_config.UpdateCmekSettingsRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            cmek_settings: Optional[logging_config.CmekSettings] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.CmekSettings:
        r"""Updates the Log Router CMEK settings for the given resource.

        Note: CMEK for the Log Router can currently only be configured
        for Google Cloud organizations. Once configured, it applies to
        all projects and folders in the Google Cloud organization.

        [UpdateCmekSettings][google.logging.v2.ConfigServiceV2.UpdateCmekSettings]
        fails when any of the following are true:

        -  The value of ``kms_key_name`` is invalid.
        -  The associated service account doesn't have the required
           ``roles/cloudkms.cryptoKeyEncrypterDecrypter`` role assigned
           for the key.
        -  Access to the key is disabled.

        See `Enabling CMEK for Log
        Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
        for more information.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_update_cmek_settings():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.UpdateCmekSettingsRequest(
                    name="name_value",
                )

                # Make the request
                response = client.update_cmek_settings(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateCmekSettingsRequest, dict]):
                The request object. The parameters to
                [UpdateCmekSettings][google.logging.v2.ConfigServiceV2.UpdateCmekSettings].

                See `Enabling CMEK for Log
                Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.
            name (str):
                Required. The resource name for the CMEK settings to
                update.

                ::

                    "projects/[PROJECT_ID]/cmekSettings"
                    "organizations/[ORGANIZATION_ID]/cmekSettings"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/cmekSettings"
                    "folders/[FOLDER_ID]/cmekSettings"

                For example:

                ``"organizations/12345/cmekSettings"``

                Note: CMEK for the Log Router can currently only be
                configured for Google Cloud organizations. Once
                configured, it applies to all projects and folders in
                the Google Cloud organization.

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            cmek_settings (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CmekSettings):
                Required. The CMEK settings to update.

                See `Enabling CMEK for Log
                Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.

                This corresponds to the ``cmek_settings`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (google.protobuf.field_mask_pb2.FieldMask):
                Optional. Field mask identifying which fields from
                ``cmek_settings`` should be updated. A field will be
                overwritten if and only if it is in the update mask.
                Output only fields cannot be updated.

                See [FieldMask][google.protobuf.FieldMask] for more
                information.

                For example: ``"updateMask=kmsKeyName"``

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CmekSettings:
                Describes the customer-managed encryption key (CMEK) settings associated with
                   a project, folder, organization, billing account, or
                   flexible resource.

                   Note: CMEK for the Log Router can currently only be
                   configured for Google Cloud organizations. Once
                   configured, it applies to all projects and folders in
                   the Google Cloud organization.

                   See [Enabling CMEK for Log
                   Router](\ https://cloud.google.com/logging/docs/routing/managed-encryption)
                   for more information.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name, cmek_settings, update_mask])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.UpdateCmekSettingsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.UpdateCmekSettingsRequest):
            request = logging_config.UpdateCmekSettingsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name
            if cmek_settings is not None:
                request.cmek_settings = cmek_settings
            if update_mask is not None:
                request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.update_cmek_settings]

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

    def get_settings(self,
            request: Optional[Union[logging_config.GetSettingsRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.Settings:
        r"""Gets the settings for the given resource.

        Note: Settings can be retrieved for Google Cloud projects,
        folders, organizations, and billing accounts.

        See [View default resource settings for Logging]
        (https://cloud.google.com/logging/docs/default-settings#view-org-settings)
        for more information.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_get_settings():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.GetSettingsRequest(
                    name="name_value",
                )

                # Make the request
                response = client.get_settings(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetSettingsRequest, dict]):
                The request object. The parameters to
                [GetSettings][google.logging.v2.ConfigServiceV2.GetSettings].

                See [View default resource settings for Logging]
                (https://cloud.google.com/logging/docs/default-settings#view-org-settings)
                for more information.
            name (str):
                Required. The resource for which to retrieve settings.

                ::

                    "projects/[PROJECT_ID]/settings"
                    "organizations/[ORGANIZATION_ID]/settings"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/settings"
                    "folders/[FOLDER_ID]/settings"

                For example:

                ``"organizations/12345/settings"``

                Note: Settings can be retrieved for Google Cloud
                projects, folders, organizations, and billing accounts.

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Settings:
                Describes the settings associated
                with a project, folder, organization, or
                billing account.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.GetSettingsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.GetSettingsRequest):
            request = logging_config.GetSettingsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.get_settings]

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

    def update_settings(self,
            request: Optional[Union[logging_config.UpdateSettingsRequest, dict]] = None,
            *,
            settings: Optional[logging_config.Settings] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.Settings:
        r"""Updates the settings for the given resource. This method applies
        to all feature configurations for organization and folders.

        [UpdateSettings][google.logging.v2.ConfigServiceV2.UpdateSettings]
        fails when any of the following are true:

        -  The value of ``storage_location`` either isn't supported by
           Logging or violates the location OrgPolicy.
        -  The ``default_sink_config`` field is set, but it has an
           unspecified filter write mode.
        -  The value of ``kms_key_name`` is invalid.
        -  The associated service account doesn't have the required
           ``roles/cloudkms.cryptoKeyEncrypterDecrypter`` role assigned
           for the key.
        -  Access to the key is disabled.

        See [Configure default settings for organizations and folders]
        (https://cloud.google.com/logging/docs/default-settings) for
        more information.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_update_settings():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.UpdateSettingsRequest(
                    name="name_value",
                )

                # Make the request
                response = client.update_settings(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateSettingsRequest, dict]):
                The request object. The parameters to
                [UpdateSettings][google.logging.v2.ConfigServiceV2.UpdateSettings].

                See [Configure default settings for organizations and
                folders]
                (https://cloud.google.com/logging/docs/default-settings)
                for more information.
            settings (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Settings):
                Required. The settings to update.

                See `Enabling CMEK for Log
                Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.

                This corresponds to the ``settings`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (google.protobuf.field_mask_pb2.FieldMask):
                Optional. Field mask identifying which fields from
                ``settings`` should be updated. A field will be
                overwritten if and only if it is in the update mask.
                Output only fields cannot be updated.

                See [FieldMask][google.protobuf.FieldMask] for more
                information.

                For example: ``"updateMask=kmsKeyName"``

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            name (str):
                Required. The resource name for the settings to update.

                ::

                    "organizations/[ORGANIZATION_ID]/settings"

                For example:

                ``"organizations/12345/settings"``

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Settings:
                Describes the settings associated
                with a project, folder, organization, or
                billing account.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([settings, update_mask, name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.UpdateSettingsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.UpdateSettingsRequest):
            request = logging_config.UpdateSettingsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if settings is not None:
                request.settings = settings
            if update_mask is not None:
                request.update_mask = update_mask
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.update_settings]

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

    def list_saved_queries(self,
            request: Optional[Union[logging_config.ListSavedQueriesRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListSavedQueriesPager:
        r"""Lists the SavedQueries that were created by the user
        making the request.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_list_saved_queries():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.ListSavedQueriesRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_saved_queries(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSavedQueriesRequest, dict]):
                The request object. The parameters to 'ListSavedQueries'.
            parent (str):
                Required. The resource to which the listed queries
                belong.

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]"

                For example:

                ::

                    "projects/my-project/locations/us-central1"

                Note: The locations portion of the resource must be
                specified. To get a list of all saved queries, a
                wildcard character ``-`` can be used for [LOCATION_ID],
                for example:

                ::

                    "projects/my-project/locations/-"

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListSavedQueriesPager:
                The response from ListSavedQueries.

                Iterating over this object will yield
                results and resolve additional pages
                automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.ListSavedQueriesRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.ListSavedQueriesRequest):
            request = logging_config.ListSavedQueriesRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_saved_queries]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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
        response = pagers.ListSavedQueriesPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def create_saved_query(self,
            request: Optional[Union[logging_config.CreateSavedQueryRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            saved_query: Optional[logging_config.SavedQuery] = None,
            saved_query_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging_config.SavedQuery:
        r"""Creates a new SavedQuery for the user making the
        request.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_create_saved_query():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                saved_query = logging_v2.SavedQuery()
                saved_query.logging_query.summary_field_start = 2046
                saved_query.logging_query.filter = "filter_value"
                saved_query.display_name = "display_name_value"
                saved_query.visibility = "SHARED"

                request = logging_v2.CreateSavedQueryRequest(
                    parent="parent_value",
                    saved_query=saved_query,
                )

                # Make the request
                response = client.create_saved_query(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateSavedQueryRequest, dict]):
                The request object. The parameters to 'CreateSavedQuery'.
            parent (str):
                Required. The parent resource in which to create the
                saved query:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]"

                For example:

                ::

                    "projects/my-project/locations/global"
                    "organizations/123456789/locations/us-central1"

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            saved_query (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.SavedQuery):
                Required. The new saved query.
                This corresponds to the ``saved_query`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            saved_query_id (str):
                Optional. The ID to use for the saved query, which will
                become the final component of the saved query's resource
                name.

                If the ``saved_query_id`` is not provided, the system
                will generate an alphanumeric ID.

                The ``saved_query_id`` is limited to 100 characters and
                can include only the following characters:

                -  upper and lower-case alphanumeric characters,
                -  underscores,
                -  hyphens,
                -  periods.

                First character has to be alphanumeric.

                This corresponds to the ``saved_query_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.SavedQuery:
                Describes a query that has been saved
                by a user.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent, saved_query, saved_query_id])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.CreateSavedQueryRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.CreateSavedQueryRequest):
            request = logging_config.CreateSavedQueryRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent
            if saved_query is not None:
                request.saved_query = saved_query
            if saved_query_id is not None:
                request.saved_query_id = saved_query_id

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.create_saved_query]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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

    def delete_saved_query(self,
            request: Optional[Union[logging_config.DeleteSavedQueryRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Deletes an existing SavedQuery that was created by
        the user making the request.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_delete_saved_query():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.DeleteSavedQueryRequest(
                    name="name_value",
                )

                # Make the request
                client.delete_saved_query(request=request)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteSavedQueryRequest, dict]):
                The request object. The parameters to 'DeleteSavedQuery'.
            name (str):
                Required. The full resource name of the saved query to
                delete.

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]/savedQueries/[QUERY_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/savedQueries/[QUERY_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/savedQueries/[QUERY_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]/savedQueries/[QUERY_ID]"

                For example:

                ::

                    "projects/my-project/locations/global/savedQueries/my-saved-query"

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
        # in a logging_config.DeleteSavedQueryRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.DeleteSavedQueryRequest):
            request = logging_config.DeleteSavedQueryRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if name is not None:
                request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.delete_saved_query]

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

    def list_recent_queries(self,
            request: Optional[Union[logging_config.ListRecentQueriesRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListRecentQueriesPager:
        r"""Lists the RecentQueries that were created by the user
        making the request.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_list_recent_queries():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.ListRecentQueriesRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_recent_queries(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListRecentQueriesRequest, dict]):
                The request object. The parameters to
                'ListRecentQueries'.
            parent (str):
                Required. The resource to which the listed queries
                belong.

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]"
                    "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]"
                    "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]"
                    "folders/[FOLDER_ID]/locations/[LOCATION_ID]"

                For example:

                ``projects/my-project/locations/us-central1``

                Note: The location portion of the resource must be
                specified, but supplying the character ``-`` in place of
                [LOCATION_ID] will return all recent queries.

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListRecentQueriesPager:
                The response from ListRecentQueries.

                Iterating over this object will yield
                results and resolve additional pages
                automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.ListRecentQueriesRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.ListRecentQueriesRequest):
            request = logging_config.ListRecentQueriesRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_recent_queries]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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
        response = pagers.ListRecentQueriesPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def copy_log_entries(self,
            request: Optional[Union[logging_config.CopyLogEntriesRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> operation.Operation:
        r"""Copies a set of log entries from a log bucket to a
        Cloud Storage bucket.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_copy_log_entries():
                # Create a client
                client = logging_v2.ConfigServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.CopyLogEntriesRequest(
                    name="name_value",
                    destination="destination_value",
                )

                # Make the request
                operation = client.copy_log_entries(request=request)

                print("Waiting for operation to complete...")

                response = operation.result()

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CopyLogEntriesRequest, dict]):
                The request object. The parameters to CopyLogEntries.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.api_core.operation.Operation:
                An object representing a long-running operation.

                The result type for the operation will be
                :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CopyLogEntriesResponse`
                Response type for CopyLogEntries long running
                operations.

        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a logging_config.CopyLogEntriesRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging_config.CopyLogEntriesRequest):
            request = logging_config.CopyLogEntriesRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.copy_log_entries]

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Wrap the response in an operation future.
        response = operation.from_gapic(
            response,
            self._transport.operations_client,
            logging_config.CopyLogEntriesResponse,
            metadata_type=logging_config.CopyLogEntriesMetadata,
        )

        # Done; return the response.
        return response

    def __enter__(self) -> "ConfigServiceV2Client":
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
    "ConfigServiceV2Client",
)
