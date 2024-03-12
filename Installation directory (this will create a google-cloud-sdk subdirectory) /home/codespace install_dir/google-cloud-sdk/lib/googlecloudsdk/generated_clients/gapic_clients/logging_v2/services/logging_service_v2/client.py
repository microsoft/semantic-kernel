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
from typing import Dict, Mapping, MutableMapping, MutableSequence, Optional, Iterable, Iterator, Sequence, Tuple, Type, Union, cast

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

from google.api import monitored_resource_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.logging_service_v2 import pagers
from googlecloudsdk.generated_clients.gapic_clients.logging_v2.types import log_entry
from googlecloudsdk.generated_clients.gapic_clients.logging_v2.types import logging
from .transports.base import LoggingServiceV2Transport, DEFAULT_CLIENT_INFO
from .transports.grpc import LoggingServiceV2GrpcTransport
from .transports.grpc_asyncio import LoggingServiceV2GrpcAsyncIOTransport
from .transports.rest import LoggingServiceV2RestTransport


class LoggingServiceV2ClientMeta(type):
    """Metaclass for the LoggingServiceV2 client.

    This provides class-level methods for building and retrieving
    support objects (e.g. transport) without polluting the client instance
    objects.
    """
    _transport_registry = OrderedDict()  # type: Dict[str, Type[LoggingServiceV2Transport]]
    _transport_registry["grpc"] = LoggingServiceV2GrpcTransport
    _transport_registry["grpc_asyncio"] = LoggingServiceV2GrpcAsyncIOTransport
    _transport_registry["rest"] = LoggingServiceV2RestTransport

    def get_transport_class(cls,
            label: Optional[str] = None,
        ) -> Type[LoggingServiceV2Transport]:
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


class LoggingServiceV2Client(metaclass=LoggingServiceV2ClientMeta):
    """Service for storing and querying logs."""

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
            LoggingServiceV2Client: The constructed client.
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
            LoggingServiceV2Client: The constructed client.
        """
        credentials = service_account.Credentials.from_service_account_file(
            filename)
        kwargs["credentials"] = credentials
        return cls(*args, **kwargs)

    from_service_account_json = from_service_account_file

    @property
    def transport(self) -> LoggingServiceV2Transport:
        """Returns the transport used by the client instance.

        Returns:
            LoggingServiceV2Transport: The transport used by the client
                instance.
        """
        return self._transport

    @staticmethod
    def log_path(project: str,log: str,) -> str:
        """Returns a fully-qualified log string."""
        return "projects/{project}/logs/{log}".format(project=project, log=log, )

    @staticmethod
    def parse_log_path(path: str) -> Dict[str,str]:
        """Parses a log path into its component segments."""
        m = re.match(r"^projects/(?P<project>.+?)/logs/(?P<log>.+?)$", path)
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
            transport: Optional[Union[str, LoggingServiceV2Transport]] = None,
            client_options: Optional[Union[client_options_lib.ClientOptions, dict]] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            ) -> None:
        """Instantiates the logging service v2 client.

        Args:
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
            transport (Union[str, LoggingServiceV2Transport]): The
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
        if isinstance(transport, LoggingServiceV2Transport):
            # transport is a LoggingServiceV2Transport instance.
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

    def delete_log(self,
            request: Optional[Union[logging.DeleteLogRequest, dict]] = None,
            *,
            log_name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Deletes all the log entries in a log for the \_Default Log
        Bucket. The log reappears if it receives new entries. Log
        entries written shortly before the delete operation might not be
        deleted. Entries received after the delete operation with a
        timestamp before the operation will be deleted.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_delete_log():
                # Create a client
                client = logging_v2.LoggingServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.DeleteLogRequest(
                    log_name="log_name_value",
                )

                # Make the request
                client.delete_log(request=request)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteLogRequest, dict]):
                The request object. The parameters to DeleteLog.
            log_name (str):
                Required. The resource name of the log to delete:

                -  ``projects/[PROJECT_ID]/logs/[LOG_ID]``
                -  ``organizations/[ORGANIZATION_ID]/logs/[LOG_ID]``
                -  ``billingAccounts/[BILLING_ACCOUNT_ID]/logs/[LOG_ID]``
                -  ``folders/[FOLDER_ID]/logs/[LOG_ID]``

                ``[LOG_ID]`` must be URL-encoded. For example,
                ``"projects/my-project-id/logs/syslog"``,
                ``"organizations/123/logs/cloudaudit.googleapis.com%2Factivity"``.

                For more information about log names, see
                [LogEntry][google.logging.v2.LogEntry].

                This corresponds to the ``log_name`` field
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
        has_flattened_params = any([log_name])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging.DeleteLogRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging.DeleteLogRequest):
            request = logging.DeleteLogRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if log_name is not None:
                request.log_name = log_name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.delete_log]

         # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("log_name", request.log_name),
            )),
        )

        # Send the request.
        rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    def write_log_entries(self,
            request: Optional[Union[logging.WriteLogEntriesRequest, dict]] = None,
            *,
            log_name: Optional[str] = None,
            resource: Optional[monitored_resource_pb2.MonitoredResource] = None,
            labels: Optional[MutableMapping[str, str]] = None,
            entries: Optional[MutableSequence[log_entry.LogEntry]] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> logging.WriteLogEntriesResponse:
        r"""Writes log entries to Logging. This API method is the only way
        to send log entries to Logging. This method is used, directly or
        indirectly, by the Logging agent (fluentd) and all logging
        libraries configured to use Logging. A single request may
        contain log entries for a maximum of 1000 different resource
        names (projects, organizations, billing accounts or folders),
        where the resource name for a log entry is determined from its
        ``logName`` field.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_write_log_entries():
                # Create a client
                client = logging_v2.LoggingServiceV2Client()

                # Initialize request argument(s)
                entries = logging_v2.LogEntry()
                entries.log_name = "log_name_value"

                request = logging_v2.WriteLogEntriesRequest(
                    entries=entries,
                )

                # Make the request
                response = client.write_log_entries(request=request)

                # Handle the response
                print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.WriteLogEntriesRequest, dict]):
                The request object. The parameters to WriteLogEntries.
            log_name (str):
                Optional. A default log resource name that is assigned
                to all log entries in ``entries`` that do not specify a
                value for ``log_name``:

                -  ``projects/[PROJECT_ID]/logs/[LOG_ID]``
                -  ``organizations/[ORGANIZATION_ID]/logs/[LOG_ID]``
                -  ``billingAccounts/[BILLING_ACCOUNT_ID]/logs/[LOG_ID]``
                -  ``folders/[FOLDER_ID]/logs/[LOG_ID]``

                ``[LOG_ID]`` must be URL-encoded. For example:

                ::

                    "projects/my-project-id/logs/syslog"
                    "organizations/123/logs/cloudaudit.googleapis.com%2Factivity"

                The permission ``logging.logEntries.create`` is needed
                on each project, organization, billing account, or
                folder that is receiving new log entries, whether the
                resource is specified in ``logName`` or in an individual
                log entry.

                This corresponds to the ``log_name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            resource (google.api.monitored_resource_pb2.MonitoredResource):
                Optional. A default monitored resource object that is
                assigned to all log entries in ``entries`` that do not
                specify a value for ``resource``. Example:

                ::

                    { "type": "gce_instance",
                      "labels": {
                        "zone": "us-central1-a", "instance_id": "00000000000000000000" }}

                See [LogEntry][google.logging.v2.LogEntry].

                This corresponds to the ``resource`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            labels (MutableMapping[str, str]):
                Optional. Default labels that are added to the
                ``labels`` field of all log entries in ``entries``. If a
                log entry already has a label with the same key as a
                label in this parameter, then the log entry's label is
                not changed. See [LogEntry][google.logging.v2.LogEntry].

                This corresponds to the ``labels`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            entries (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogEntry]):
                Required. The log entries to send to Logging. The order
                of log entries in this list does not matter. Values
                supplied in this method's ``log_name``, ``resource``,
                and ``labels`` fields are copied into those log entries
                in this list that do not include values for their
                corresponding fields. For more information, see the
                [LogEntry][google.logging.v2.LogEntry] type.

                If the ``timestamp`` or ``insert_id`` fields are missing
                in log entries, then this method supplies the current
                time or a unique identifier, respectively. The supplied
                values are chosen so that, among the log entries that
                did not supply their own values, the entries earlier in
                the list will sort before the entries later in the list.
                See the ``entries.list`` method.

                Log entries with timestamps that are more than the `logs
                retention
                period <https://cloud.google.com/logging/quotas>`__ in
                the past or more than 24 hours in the future will not be
                available when calling ``entries.list``. However, those
                log entries can still be `exported with
                LogSinks <https://cloud.google.com/logging/docs/api/tasks/exporting-logs>`__.

                To improve throughput and to avoid exceeding the `quota
                limit <https://cloud.google.com/logging/quotas>`__ for
                calls to ``entries.write``, you should try to include
                several log entries in this list, rather than calling
                this method for each individual log entry.

                This corresponds to the ``entries`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.WriteLogEntriesResponse:
                Result returned from WriteLogEntries.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([log_name, resource, labels, entries])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging.WriteLogEntriesRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging.WriteLogEntriesRequest):
            request = logging.WriteLogEntriesRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if log_name is not None:
                request.log_name = log_name
            if resource is not None:
                request.resource = resource
            if labels is not None:
                request.labels = labels
            if entries is not None:
                request.entries = entries

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.write_log_entries]

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def list_log_entries(self,
            request: Optional[Union[logging.ListLogEntriesRequest, dict]] = None,
            *,
            resource_names: Optional[MutableSequence[str]] = None,
            filter: Optional[str] = None,
            order_by: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListLogEntriesPager:
        r"""Lists log entries. Use this method to retrieve log entries that
        originated from a project/folder/organization/billing account.
        For ways to export log entries, see `Exporting
        Logs <https://cloud.google.com/logging/docs/export>`__.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_list_log_entries():
                # Create a client
                client = logging_v2.LoggingServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.ListLogEntriesRequest(
                    resource_names=['resource_names_value1', 'resource_names_value2'],
                )

                # Make the request
                page_result = client.list_log_entries(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLogEntriesRequest, dict]):
                The request object. The parameters to ``ListLogEntries``.
            resource_names (MutableSequence[str]):
                Required. Names of one or more parent resources from
                which to retrieve log entries:

                -  ``projects/[PROJECT_ID]``
                -  ``organizations/[ORGANIZATION_ID]``
                -  ``billingAccounts/[BILLING_ACCOUNT_ID]``
                -  ``folders/[FOLDER_ID]``

                May alternatively be one or more views:

                -  ``projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
                -  ``organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
                -  ``billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
                -  ``folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``

                Projects listed in the ``project_ids`` field are added
                to this list. A maximum of 100 resources may be
                specified in a single request.

                This corresponds to the ``resource_names`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            filter (str):
                Optional. A filter that chooses which log entries to
                return. For more information, see [Logging query
                language]
                (https://cloud.google.com/logging/docs/view/logging-query-language).

                Only log entries that match the filter are returned. An
                empty filter matches all log entries in the resources
                listed in ``resource_names``. Referencing a parent
                resource that is not listed in ``resource_names`` will
                cause the filter to return no results. The maximum
                length of a filter is 20,000 characters.

                This corresponds to the ``filter`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            order_by (str):
                Optional. How the results should be sorted. Presently,
                the only permitted values are ``"timestamp asc"``
                (default) and ``"timestamp desc"``. The first option
                returns entries in order of increasing values of
                ``LogEntry.timestamp`` (oldest first), and the second
                option returns entries in order of decreasing timestamps
                (newest first). Entries with equal timestamps are
                returned in order of their ``insert_id`` values.

                This corresponds to the ``order_by`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.logging_service_v2.pagers.ListLogEntriesPager:
                Result returned from ListLogEntries.

                Iterating over this object will yield results and
                resolve additional pages automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([resource_names, filter, order_by])
        if request is not None and has_flattened_params:
            raise ValueError('If the `request` argument is set, then none of '
                             'the individual field arguments should be set.')

        # Minor optimization to avoid making a copy if the user passes
        # in a logging.ListLogEntriesRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging.ListLogEntriesRequest):
            request = logging.ListLogEntriesRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if resource_names is not None:
                request.resource_names = resource_names
            if filter is not None:
                request.filter = filter
            if order_by is not None:
                request.order_by = order_by

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_log_entries]

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # This method is paged; wrap the response in a pager, which provides
        # an `__iter__` convenience method.
        response = pagers.ListLogEntriesPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def list_monitored_resource_descriptors(self,
            request: Optional[Union[logging.ListMonitoredResourceDescriptorsRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListMonitoredResourceDescriptorsPager:
        r"""Lists the descriptors for monitored resource types
        used by Logging.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_list_monitored_resource_descriptors():
                # Create a client
                client = logging_v2.LoggingServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.ListMonitoredResourceDescriptorsRequest(
                )

                # Make the request
                page_result = client.list_monitored_resource_descriptors(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListMonitoredResourceDescriptorsRequest, dict]):
                The request object. The parameters to
                ListMonitoredResourceDescriptors
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.logging_service_v2.pagers.ListMonitoredResourceDescriptorsPager:
                Result returned from
                ListMonitoredResourceDescriptors.
                Iterating over this object will yield
                results and resolve additional pages
                automatically.

        """
        # Create or coerce a protobuf request object.
        # Minor optimization to avoid making a copy if the user passes
        # in a logging.ListMonitoredResourceDescriptorsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging.ListMonitoredResourceDescriptorsRequest):
            request = logging.ListMonitoredResourceDescriptorsRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_monitored_resource_descriptors]

        # Send the request.
        response = rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # This method is paged; wrap the response in a pager, which provides
        # an `__iter__` convenience method.
        response = pagers.ListMonitoredResourceDescriptorsPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def list_logs(self,
            request: Optional[Union[logging.ListLogsRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListLogsPager:
        r"""Lists the logs in projects, organizations, folders,
        or billing accounts. Only logs that have entries are
        listed.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_list_logs():
                # Create a client
                client = logging_v2.LoggingServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.ListLogsRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_logs(request=request)

                # Handle the response
                for response in page_result:
                    print(response)

        Args:
            request (Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLogsRequest, dict]):
                The request object. The parameters to ListLogs.
            parent (str):
                Required. The resource name to list logs for:

                -  ``projects/[PROJECT_ID]``
                -  ``organizations/[ORGANIZATION_ID]``
                -  ``billingAccounts/[BILLING_ACCOUNT_ID]``
                -  ``folders/[FOLDER_ID]``

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.logging_service_v2.pagers.ListLogsPager:
                Result returned from ListLogs.

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
        # in a logging.ListLogsRequest.
        # There's no risk of modifying the input as we've already verified
        # there are no flattened fields.
        if not isinstance(request, logging.ListLogsRequest):
            request = logging.ListLogsRequest(request)
            # If we have keyword arguments corresponding to fields on the
            # request, apply these.
            if parent is not None:
                request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.list_logs]

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
        response = pagers.ListLogsPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def tail_log_entries(self,
            requests: Optional[Iterator[logging.TailLogEntriesRequest]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> Iterable[logging.TailLogEntriesResponse]:
        r"""Streaming read of log entries as they are received.
        Until the stream is terminated, it will continue reading
        logs.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import logging_v2

            def sample_tail_log_entries():
                # Create a client
                client = logging_v2.LoggingServiceV2Client()

                # Initialize request argument(s)
                request = logging_v2.TailLogEntriesRequest(
                    resource_names=['resource_names_value1', 'resource_names_value2'],
                )

                # This method expects an iterator which contains
                # 'logging_v2.TailLogEntriesRequest' objects
                # Here we create a generator that yields a single `request` for
                # demonstrative purposes.
                requests = [request]

                def request_generator():
                    for request in requests:
                        yield request

                # Make the request
                stream = client.tail_log_entries(requests=request_generator())

                # Handle the response
                for response in stream:
                    print(response)

        Args:
            requests (Iterator[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.TailLogEntriesRequest]):
                The request object iterator. The parameters to ``TailLogEntries``.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            Iterable[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.TailLogEntriesResponse]:
                Result returned from TailLogEntries.
        """

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._transport._wrapped_methods[self._transport.tail_log_entries]

        # Send the request.
        response = rpc(
            requests,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def __enter__(self) -> "LoggingServiceV2Client":
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
    "LoggingServiceV2Client",
)
