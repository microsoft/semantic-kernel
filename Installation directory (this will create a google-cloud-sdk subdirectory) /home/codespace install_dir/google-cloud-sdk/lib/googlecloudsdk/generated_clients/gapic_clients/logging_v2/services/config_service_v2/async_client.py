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
from typing import Dict, Mapping, MutableMapping, MutableSequence, Optional, Sequence, Tuple, Type, Union

from googlecloudsdk.generated_clients.gapic_clients.logging_v2 import gapic_version as package_version

from google.api_core.client_options import ClientOptions
from google.api_core import exceptions as core_exceptions
from google.api_core import gapic_v1
from google.api_core import retry as retries
from google.auth import credentials as ga_credentials   # type: ignore
from google.oauth2 import service_account              # type: ignore

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
from .transports.grpc_asyncio import ConfigServiceV2GrpcAsyncIOTransport
from .client import ConfigServiceV2Client


class ConfigServiceV2AsyncClient:
    """Service for configuring sinks used to route log entries."""

    _client: ConfigServiceV2Client

    DEFAULT_ENDPOINT = ConfigServiceV2Client.DEFAULT_ENDPOINT
    DEFAULT_MTLS_ENDPOINT = ConfigServiceV2Client.DEFAULT_MTLS_ENDPOINT

    cmek_settings_path = staticmethod(ConfigServiceV2Client.cmek_settings_path)
    parse_cmek_settings_path = staticmethod(ConfigServiceV2Client.parse_cmek_settings_path)
    link_path = staticmethod(ConfigServiceV2Client.link_path)
    parse_link_path = staticmethod(ConfigServiceV2Client.parse_link_path)
    log_bucket_path = staticmethod(ConfigServiceV2Client.log_bucket_path)
    parse_log_bucket_path = staticmethod(ConfigServiceV2Client.parse_log_bucket_path)
    log_exclusion_path = staticmethod(ConfigServiceV2Client.log_exclusion_path)
    parse_log_exclusion_path = staticmethod(ConfigServiceV2Client.parse_log_exclusion_path)
    log_sink_path = staticmethod(ConfigServiceV2Client.log_sink_path)
    parse_log_sink_path = staticmethod(ConfigServiceV2Client.parse_log_sink_path)
    log_view_path = staticmethod(ConfigServiceV2Client.log_view_path)
    parse_log_view_path = staticmethod(ConfigServiceV2Client.parse_log_view_path)
    recent_query_path = staticmethod(ConfigServiceV2Client.recent_query_path)
    parse_recent_query_path = staticmethod(ConfigServiceV2Client.parse_recent_query_path)
    saved_query_path = staticmethod(ConfigServiceV2Client.saved_query_path)
    parse_saved_query_path = staticmethod(ConfigServiceV2Client.parse_saved_query_path)
    settings_path = staticmethod(ConfigServiceV2Client.settings_path)
    parse_settings_path = staticmethod(ConfigServiceV2Client.parse_settings_path)
    common_billing_account_path = staticmethod(ConfigServiceV2Client.common_billing_account_path)
    parse_common_billing_account_path = staticmethod(ConfigServiceV2Client.parse_common_billing_account_path)
    common_folder_path = staticmethod(ConfigServiceV2Client.common_folder_path)
    parse_common_folder_path = staticmethod(ConfigServiceV2Client.parse_common_folder_path)
    common_organization_path = staticmethod(ConfigServiceV2Client.common_organization_path)
    parse_common_organization_path = staticmethod(ConfigServiceV2Client.parse_common_organization_path)
    common_project_path = staticmethod(ConfigServiceV2Client.common_project_path)
    parse_common_project_path = staticmethod(ConfigServiceV2Client.parse_common_project_path)
    common_location_path = staticmethod(ConfigServiceV2Client.common_location_path)
    parse_common_location_path = staticmethod(ConfigServiceV2Client.parse_common_location_path)

    @classmethod
    def from_service_account_info(cls, info: dict, *args, **kwargs):
        """Creates an instance of this client using the provided credentials
            info.

        Args:
            info (dict): The service account private key info.
            args: Additional arguments to pass to the constructor.
            kwargs: Additional arguments to pass to the constructor.

        Returns:
            ConfigServiceV2AsyncClient: The constructed client.
        """
        return ConfigServiceV2Client.from_service_account_info.__func__(ConfigServiceV2AsyncClient, info, *args, **kwargs)  # type: ignore

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
            ConfigServiceV2AsyncClient: The constructed client.
        """
        return ConfigServiceV2Client.from_service_account_file.__func__(ConfigServiceV2AsyncClient, filename, *args, **kwargs)  # type: ignore

    from_service_account_json = from_service_account_file

    @classmethod
    def get_mtls_endpoint_and_cert_source(cls, client_options: Optional[ClientOptions] = None):
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
        return ConfigServiceV2Client.get_mtls_endpoint_and_cert_source(client_options)  # type: ignore

    @property
    def transport(self) -> ConfigServiceV2Transport:
        """Returns the transport used by the client instance.

        Returns:
            ConfigServiceV2Transport: The transport used by the client instance.
        """
        return self._client.transport

    get_transport_class = functools.partial(type(ConfigServiceV2Client).get_transport_class, type(ConfigServiceV2Client))

    def __init__(self, *,
            credentials: Optional[ga_credentials.Credentials] = None,
            transport: Union[str, ConfigServiceV2Transport] = "grpc_asyncio",
            client_options: Optional[ClientOptions] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            ) -> None:
        """Instantiates the config service v2 client.

        Args:
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
            transport (Union[str, ~.ConfigServiceV2Transport]): The
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
        self._client = ConfigServiceV2Client(
            credentials=credentials,
            transport=transport,
            client_options=client_options,
            client_info=client_info,

        )

    async def list_buckets(self,
            request: Optional[Union[logging_config.ListBucketsRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListBucketsAsyncPager:
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

            async def sample_list_buckets():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.ListBucketsRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_buckets(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListBucketsRequest, dict]]):
                The request object. The parameters to ``ListBuckets``.
            parent (:class:`str`):
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
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListBucketsAsyncPager:
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.ListBucketsRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_buckets,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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
        response = pagers.ListBucketsAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def get_bucket(self,
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

            async def sample_get_bucket():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.GetBucketRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.get_bucket(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetBucketRequest, dict]]):
                The request object. The parameters to ``GetBucket``.
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.GetBucketRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_bucket,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def create_bucket_async(self,
            request: Optional[Union[logging_config.CreateBucketRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            bucket: Optional[logging_config.LogBucket] = None,
            bucket_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> operation_async.AsyncOperation:
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

            async def sample_create_bucket_async():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.CreateBucketRequest(
                    parent="parent_value",
                    bucket_id="bucket_id_value",
                )

                # Make the request
                operation = client.create_bucket_async(request=request)

                print("Waiting for operation to complete...")

                response = (await operation).result()

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateBucketRequest, dict]]):
                The request object. The parameters to ``CreateBucket``.
            parent (:class:`str`):
                Required. The resource in which to create the log
                bucket:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]"

                For example:

                ``"projects/my-project/locations/global"``

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket`):
                Required. The new bucket. The region
                specified in the new bucket must be
                compliant with any Location Restriction
                Org Policy. The name field in the bucket
                is ignored.

                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket_id (:class:`str`):
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
            google.api_core.operation_async.AsyncOperation:
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_bucket_async,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Wrap the response in an operation future.
        response = operation_async.from_gapic(
            response,
            self._client._transport.operations_client,
            logging_config.LogBucket,
            metadata_type=logging_config.BucketMetadata,
        )

        # Done; return the response.
        return response

    async def update_bucket_async(self,
            request: Optional[Union[logging_config.UpdateBucketRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            bucket: Optional[logging_config.LogBucket] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> operation_async.AsyncOperation:
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

            async def sample_update_bucket_async():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.UpdateBucketRequest(
                    name="name_value",
                )

                # Make the request
                operation = client.update_bucket_async(request=request)

                print("Waiting for operation to complete...")

                response = (await operation).result()

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateBucketRequest, dict]]):
                The request object. The parameters to ``UpdateBucket``.
            name (:class:`str`):
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
            bucket (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket`):
                Required. The updated bucket.
                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
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
            google.api_core.operation_async.AsyncOperation:
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_bucket_async,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Wrap the response in an operation future.
        response = operation_async.from_gapic(
            response,
            self._client._transport.operations_client,
            logging_config.LogBucket,
            metadata_type=logging_config.BucketMetadata,
        )

        # Done; return the response.
        return response

    async def create_bucket(self,
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

            async def sample_create_bucket():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.CreateBucketRequest(
                    parent="parent_value",
                    bucket_id="bucket_id_value",
                )

                # Make the request
                response = await client.create_bucket(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateBucketRequest, dict]]):
                The request object. The parameters to ``CreateBucket``.
            parent (:class:`str`):
                Required. The resource in which to create the log
                bucket:

                ::

                    "projects/[PROJECT_ID]/locations/[LOCATION_ID]"

                For example:

                ``"projects/my-project/locations/global"``

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket`):
                Required. The new bucket. The region
                specified in the new bucket must be
                compliant with any Location Restriction
                Org Policy. The name field in the bucket
                is ignored.

                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket_id (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_bucket,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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

    async def update_bucket(self,
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

            async def sample_update_bucket():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.UpdateBucketRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.update_bucket(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateBucketRequest, dict]]):
                The request object. The parameters to ``UpdateBucket``.
            name (:class:`str`):
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
            bucket (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket`):
                Required. The updated bucket.
                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_bucket,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def delete_bucket(self,
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

            async def sample_delete_bucket():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.DeleteBucketRequest(
                    name="name_value",
                )

                # Make the request
                await client.delete_bucket(request=request)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteBucketRequest, dict]]):
                The request object. The parameters to ``DeleteBucket``.
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.DeleteBucketRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_bucket,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def undelete_bucket(self,
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

            async def sample_undelete_bucket():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.UndeleteBucketRequest(
                    name="name_value",
                )

                # Make the request
                await client.undelete_bucket(request=request)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UndeleteBucketRequest, dict]]):
                The request object. The parameters to ``UndeleteBucket``.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        # Create or coerce a protobuf request object.
        request = logging_config.UndeleteBucketRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.undelete_bucket,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def list_views(self,
            request: Optional[Union[logging_config.ListViewsRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListViewsAsyncPager:
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

            async def sample_list_views():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.ListViewsRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_views(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListViewsRequest, dict]]):
                The request object. The parameters to ``ListViews``.
            parent (:class:`str`):
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
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListViewsAsyncPager:
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.ListViewsRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_views,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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
        response = pagers.ListViewsAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def get_view(self,
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

            async def sample_get_view():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.GetViewRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.get_view(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetViewRequest, dict]]):
                The request object. The parameters to ``GetView``.
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.GetViewRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_view,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def create_view(self,
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

            async def sample_create_view():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.CreateViewRequest(
                    parent="parent_value",
                    view_id="view_id_value",
                )

                # Make the request
                response = await client.create_view(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateViewRequest, dict]]):
                The request object. The parameters to ``CreateView``.
            parent (:class:`str`):
                Required. The bucket in which to create the view

                ::

                    `"projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"`

                For example:

                ``"projects/my-project/locations/global/buckets/my-bucket"``

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            view (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogView`):
                Required. The new view.
                This corresponds to the ``view`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            view_id (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_view,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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

    async def update_view(self,
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

            async def sample_update_view():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.UpdateViewRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.update_view(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateViewRequest, dict]]):
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
        request = logging_config.UpdateViewRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_view,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def delete_view(self,
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

            async def sample_delete_view():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.DeleteViewRequest(
                    name="name_value",
                )

                # Make the request
                await client.delete_view(request=request)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteViewRequest, dict]]):
                The request object. The parameters to ``DeleteView``.
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.DeleteViewRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_view,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def list_exclusions(self,
            request: Optional[Union[logging_config.ListExclusionsRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListExclusionsAsyncPager:
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

            async def sample_list_exclusions():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.ListExclusionsRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_exclusions(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListExclusionsRequest, dict]]):
                The request object. The parameters to ``ListExclusions``.
            parent (:class:`str`):
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
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListExclusionsAsyncPager:
                Result returned from ListExclusions.

                Iterating over this object will yield results and
                resolve additional pages automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.ListExclusionsRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_exclusions,
            default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                predicate=retries.if_exception_type(
                    core_exceptions.DeadlineExceeded,
                    core_exceptions.InternalServerError,
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
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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
        response = pagers.ListExclusionsAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def get_exclusion(self,
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

            async def sample_get_exclusion():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.GetExclusionRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.get_exclusion(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetExclusionRequest, dict]]):
                The request object. The parameters to ``GetExclusion``.
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.GetExclusionRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_exclusion,
            default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                predicate=retries.if_exception_type(
                    core_exceptions.DeadlineExceeded,
                    core_exceptions.InternalServerError,
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
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def create_exclusion(self,
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

            async def sample_create_exclusion():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                exclusion = logging_v2.LogExclusion()
                exclusion.filter = "filter_value"

                request = logging_v2.CreateExclusionRequest(
                    parent="parent_value",
                    exclusion=exclusion,
                )

                # Make the request
                response = await client.create_exclusion(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateExclusionRequest, dict]]):
                The request object. The parameters to ``CreateExclusion``.
            parent (:class:`str`):
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
            exclusion (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.CreateExclusionRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent
        if exclusion is not None:
            request.exclusion = exclusion

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_exclusion,
            default_timeout=120.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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

    async def update_exclusion(self,
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

            async def sample_update_exclusion():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                exclusion = logging_v2.LogExclusion()
                exclusion.filter = "filter_value"

                request = logging_v2.UpdateExclusionRequest(
                    name="name_value",
                    exclusion=exclusion,
                )

                # Make the request
                response = await client.update_exclusion(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateExclusionRequest, dict]]):
                The request object. The parameters to ``UpdateExclusion``.
            name (:class:`str`):
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
            exclusion (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion`):
                Required. New values for the existing exclusion. Only
                the fields specified in ``update_mask`` are relevant.

                This corresponds to the ``exclusion`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_exclusion,
            default_timeout=120.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def delete_exclusion(self,
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

            async def sample_delete_exclusion():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.DeleteExclusionRequest(
                    name="name_value",
                )

                # Make the request
                await client.delete_exclusion(request=request)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteExclusionRequest, dict]]):
                The request object. The parameters to ``DeleteExclusion``.
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.DeleteExclusionRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_exclusion,
            default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                predicate=retries.if_exception_type(
                    core_exceptions.DeadlineExceeded,
                    core_exceptions.InternalServerError,
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
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def list_sinks(self,
            request: Optional[Union[logging_config.ListSinksRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListSinksAsyncPager:
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

            async def sample_list_sinks():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.ListSinksRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_sinks(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSinksRequest, dict]]):
                The request object. The parameters to ``ListSinks``.
            parent (:class:`str`):
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
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListSinksAsyncPager:
                Result returned from ListSinks.

                Iterating over this object will yield results and
                resolve additional pages automatically.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.ListSinksRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_sinks,
            default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                predicate=retries.if_exception_type(
                    core_exceptions.DeadlineExceeded,
                    core_exceptions.InternalServerError,
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
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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
        response = pagers.ListSinksAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def get_sink(self,
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

            async def sample_get_sink():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.GetSinkRequest(
                    sink_name="sink_name_value",
                )

                # Make the request
                response = await client.get_sink(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetSinkRequest, dict]]):
                The request object. The parameters to ``GetSink``.
            sink_name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.GetSinkRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if sink_name is not None:
            request.sink_name = sink_name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_sink,
            default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                predicate=retries.if_exception_type(
                    core_exceptions.DeadlineExceeded,
                    core_exceptions.InternalServerError,
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
            gapic_v1.routing_header.to_grpc_metadata((
                ("sink_name", request.sink_name),
            )),
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

    async def create_sink(self,
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

            async def sample_create_sink():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                sink = logging_v2.LogSink()
                sink.destination = "destination_value"

                request = logging_v2.CreateSinkRequest(
                    parent="parent_value",
                    sink=sink,
                )

                # Make the request
                response = await client.create_sink(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateSinkRequest, dict]]):
                The request object. The parameters to ``CreateSink``.
            parent (:class:`str`):
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
            sink (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.CreateSinkRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent
        if sink is not None:
            request.sink = sink

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_sink,
            default_timeout=120.0,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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

    async def update_sink(self,
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

            async def sample_update_sink():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                sink = logging_v2.LogSink()
                sink.destination = "destination_value"

                request = logging_v2.UpdateSinkRequest(
                    sink_name="sink_name_value",
                    sink=sink,
                )

                # Make the request
                response = await client.update_sink(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateSinkRequest, dict]]):
                The request object. The parameters to ``UpdateSink``.
            sink_name (:class:`str`):
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
            sink (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink`):
                Required. The updated sink, whose name is the same
                identifier that appears as part of ``sink_name``.

                This corresponds to the ``sink`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_sink,
            default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                predicate=retries.if_exception_type(
                    core_exceptions.DeadlineExceeded,
                    core_exceptions.InternalServerError,
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
            gapic_v1.routing_header.to_grpc_metadata((
                ("sink_name", request.sink_name),
            )),
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

    async def delete_sink(self,
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

            async def sample_delete_sink():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.DeleteSinkRequest(
                    sink_name="sink_name_value",
                )

                # Make the request
                await client.delete_sink(request=request)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteSinkRequest, dict]]):
                The request object. The parameters to ``DeleteSink``.
            sink_name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.DeleteSinkRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if sink_name is not None:
            request.sink_name = sink_name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_sink,
            default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                predicate=retries.if_exception_type(
                    core_exceptions.DeadlineExceeded,
                    core_exceptions.InternalServerError,
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
            gapic_v1.routing_header.to_grpc_metadata((
                ("sink_name", request.sink_name),
            )),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def list_links(self,
            request: Optional[Union[logging_config.ListLinksRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListLinksAsyncPager:
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

            async def sample_list_links():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.ListLinksRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_links(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListLinksRequest, dict]]):
                The request object. The parameters to ListLinks.
            parent (:class:`str`):
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
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListLinksAsyncPager:
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.ListLinksRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_links,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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
        response = pagers.ListLinksAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def get_link(self,
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

            async def sample_get_link():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.GetLinkRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.get_link(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetLinkRequest, dict]]):
                The request object. The parameters to GetLink.
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.GetLinkRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_link,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def create_link(self,
            request: Optional[Union[logging_config.CreateLinkRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            link: Optional[logging_config.Link] = None,
            link_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> operation_async.AsyncOperation:
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

            async def sample_create_link():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.CreateLinkRequest(
                    parent="parent_value",
                    link_id="link_id_value",
                )

                # Make the request
                operation = client.create_link(request=request)

                print("Waiting for operation to complete...")

                response = (await operation).result()

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateLinkRequest, dict]]):
                The request object. The parameters to CreateLink.
            parent (:class:`str`):
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
            link (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Link`):
                Required. The new link.
                This corresponds to the ``link`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            link_id (:class:`str`):
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
            google.api_core.operation_async.AsyncOperation:
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_link,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Wrap the response in an operation future.
        response = operation_async.from_gapic(
            response,
            self._client._transport.operations_client,
            logging_config.Link,
            metadata_type=logging_config.LinkMetadata,
        )

        # Done; return the response.
        return response

    async def delete_link(self,
            request: Optional[Union[logging_config.DeleteLinkRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> operation_async.AsyncOperation:
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

            async def sample_delete_link():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.DeleteLinkRequest(
                    name="name_value",
                )

                # Make the request
                operation = client.delete_link(request=request)

                print("Waiting for operation to complete...")

                response = (await operation).result()

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteLinkRequest, dict]]):
                The request object. The parameters to DeleteLink.
            name (:class:`str`):
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
            google.api_core.operation_async.AsyncOperation:
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.DeleteLinkRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_link,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Wrap the response in an operation future.
        response = operation_async.from_gapic(
            response,
            self._client._transport.operations_client,
            empty_pb2.Empty,
            metadata_type=logging_config.LinkMetadata,
        )

        # Done; return the response.
        return response

    async def get_cmek_settings(self,
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

            async def sample_get_cmek_settings():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.GetCmekSettingsRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.get_cmek_settings(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetCmekSettingsRequest, dict]]):
                The request object. The parameters to
                [GetCmekSettings][google.logging.v2.ConfigServiceV2.GetCmekSettings].

                See `Enabling CMEK for Log
                Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.GetCmekSettingsRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_cmek_settings,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def update_cmek_settings(self,
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

            async def sample_update_cmek_settings():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.UpdateCmekSettingsRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.update_cmek_settings(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateCmekSettingsRequest, dict]]):
                The request object. The parameters to
                [UpdateCmekSettings][google.logging.v2.ConfigServiceV2.UpdateCmekSettings].

                See `Enabling CMEK for Log
                Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.
            name (:class:`str`):
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
            cmek_settings (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CmekSettings`):
                Required. The CMEK settings to update.

                See `Enabling CMEK for Log
                Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.

                This corresponds to the ``cmek_settings`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_cmek_settings,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def get_settings(self,
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

            async def sample_get_settings():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.GetSettingsRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.get_settings(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.GetSettingsRequest, dict]]):
                The request object. The parameters to
                [GetSettings][google.logging.v2.ConfigServiceV2.GetSettings].

                See [View default resource settings for Logging]
                (https://cloud.google.com/logging/docs/default-settings#view-org-settings)
                for more information.
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.GetSettingsRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_settings,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def update_settings(self,
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

            async def sample_update_settings():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.UpdateSettingsRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.update_settings(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateSettingsRequest, dict]]):
                The request object. The parameters to
                [UpdateSettings][google.logging.v2.ConfigServiceV2.UpdateSettings].

                See [Configure default settings for organizations and
                folders]
                (https://cloud.google.com/logging/docs/default-settings)
                for more information.
            settings (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Settings`):
                Required. The settings to update.

                See `Enabling CMEK for Log
                Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.

                This corresponds to the ``settings`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
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
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_settings,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
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

    async def list_saved_queries(self,
            request: Optional[Union[logging_config.ListSavedQueriesRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListSavedQueriesAsyncPager:
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

            async def sample_list_saved_queries():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.ListSavedQueriesRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_saved_queries(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListSavedQueriesRequest, dict]]):
                The request object. The parameters to 'ListSavedQueries'.
            parent (:class:`str`):
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
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListSavedQueriesAsyncPager:
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.ListSavedQueriesRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_saved_queries,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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
        response = pagers.ListSavedQueriesAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def create_saved_query(self,
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

            async def sample_create_saved_query():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

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
                response = await client.create_saved_query(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateSavedQueryRequest, dict]]):
                The request object. The parameters to 'CreateSavedQuery'.
            parent (:class:`str`):
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
            saved_query (:class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.SavedQuery`):
                Required. The new saved query.
                This corresponds to the ``saved_query`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            saved_query_id (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

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
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_saved_query,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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

    async def delete_saved_query(self,
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

            async def sample_delete_saved_query():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.DeleteSavedQueryRequest(
                    name="name_value",
                )

                # Make the request
                await client.delete_saved_query(request=request)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteSavedQueryRequest, dict]]):
                The request object. The parameters to 'DeleteSavedQuery'.
            name (:class:`str`):
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.DeleteSavedQueryRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_saved_query,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def list_recent_queries(self,
            request: Optional[Union[logging_config.ListRecentQueriesRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListRecentQueriesAsyncPager:
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

            async def sample_list_recent_queries():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.ListRecentQueriesRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_recent_queries(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ListRecentQueriesRequest, dict]]):
                The request object. The parameters to
                'ListRecentQueries'.
            parent (:class:`str`):
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
            googlecloudsdk.generated_clients.gapic_clients.logging_v2.services.config_service_v2.pagers.ListRecentQueriesAsyncPager:
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
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = logging_config.ListRecentQueriesRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_recent_queries,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
            )),
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
        response = pagers.ListRecentQueriesAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def copy_log_entries(self,
            request: Optional[Union[logging_config.CopyLogEntriesRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> operation_async.AsyncOperation:
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

            async def sample_copy_log_entries():
                # Create a client
                client = logging_v2.ConfigServiceV2AsyncClient()

                # Initialize request argument(s)
                request = logging_v2.CopyLogEntriesRequest(
                    name="name_value",
                    destination="destination_value",
                )

                # Make the request
                operation = client.copy_log_entries(request=request)

                print("Waiting for operation to complete...")

                response = (await operation).result()

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CopyLogEntriesRequest, dict]]):
                The request object. The parameters to CopyLogEntries.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.api_core.operation_async.AsyncOperation:
                An object representing a long-running operation.

                The result type for the operation will be
                :class:`googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CopyLogEntriesResponse`
                Response type for CopyLogEntries long running
                operations.

        """
        # Create or coerce a protobuf request object.
        request = logging_config.CopyLogEntriesRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.copy_log_entries,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Wrap the response in an operation future.
        response = operation_async.from_gapic(
            response,
            self._client._transport.operations_client,
            logging_config.CopyLogEntriesResponse,
            metadata_type=logging_config.CopyLogEntriesMetadata,
        )

        # Done; return the response.
        return response

    async def __aenter__(self) -> "ConfigServiceV2AsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.transport.close()

DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(gapic_version=package_version.__version__)


__all__ = (
    "ConfigServiceV2AsyncClient",
)
