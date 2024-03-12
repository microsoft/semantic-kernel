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
from typing import Dict, Mapping, MutableMapping, MutableSequence, Optional, AsyncIterable, Awaitable, AsyncIterator, Sequence, Tuple, Type, Union
import warnings

from googlecloudsdk.generated_clients.gapic_clients.storage_v2 import gapic_version as package_version

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

from google.iam.v1 import iam_policy_pb2  # type: ignore
from google.iam.v1 import policy_pb2  # type: ignore
from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.storage_v2.services.storage import pagers
from googlecloudsdk.generated_clients.gapic_clients.storage_v2.types import storage
from .transports.base import StorageTransport, DEFAULT_CLIENT_INFO
from .transports.grpc_asyncio import StorageGrpcAsyncIOTransport
from .client import StorageClient


class StorageAsyncClient:
    """API Overview and Naming Syntax
    ------------------------------

    The Cloud Storage gRPC API allows applications to read and write
    data through the abstractions of buckets and objects. For a
    description of these abstractions please see
    https://cloud.google.com/storage/docs.

    Resources are named as follows:

    -  Projects are referred to as they are defined by the Resource
       Manager API, using strings like ``projects/123456`` or
       ``projects/my-string-id``.

    -  Buckets are named using string names of the form:
       ``projects/{project}/buckets/{bucket}`` For globally unique
       buckets, ``_`` may be substituted for the project.

    -  Objects are uniquely identified by their name along with the name
       of the bucket they belong to, as separate strings in this API.
       For example:

       ReadObjectRequest { bucket: 'projects/_/buckets/my-bucket'
       object: 'my-object' } Note that object names can contain ``/``
       characters, which are treated as any other character (no special
       directory semantics).
    """

    _client: StorageClient

    DEFAULT_ENDPOINT = StorageClient.DEFAULT_ENDPOINT
    DEFAULT_MTLS_ENDPOINT = StorageClient.DEFAULT_MTLS_ENDPOINT

    bucket_path = staticmethod(StorageClient.bucket_path)
    parse_bucket_path = staticmethod(StorageClient.parse_bucket_path)
    crypto_key_path = staticmethod(StorageClient.crypto_key_path)
    parse_crypto_key_path = staticmethod(StorageClient.parse_crypto_key_path)
    notification_config_path = staticmethod(StorageClient.notification_config_path)
    parse_notification_config_path = staticmethod(StorageClient.parse_notification_config_path)
    common_billing_account_path = staticmethod(StorageClient.common_billing_account_path)
    parse_common_billing_account_path = staticmethod(StorageClient.parse_common_billing_account_path)
    common_folder_path = staticmethod(StorageClient.common_folder_path)
    parse_common_folder_path = staticmethod(StorageClient.parse_common_folder_path)
    common_organization_path = staticmethod(StorageClient.common_organization_path)
    parse_common_organization_path = staticmethod(StorageClient.parse_common_organization_path)
    common_project_path = staticmethod(StorageClient.common_project_path)
    parse_common_project_path = staticmethod(StorageClient.parse_common_project_path)
    common_location_path = staticmethod(StorageClient.common_location_path)
    parse_common_location_path = staticmethod(StorageClient.parse_common_location_path)

    @classmethod
    def from_service_account_info(cls, info: dict, *args, **kwargs):
        """Creates an instance of this client using the provided credentials
            info.

        Args:
            info (dict): The service account private key info.
            args: Additional arguments to pass to the constructor.
            kwargs: Additional arguments to pass to the constructor.

        Returns:
            StorageAsyncClient: The constructed client.
        """
        return StorageClient.from_service_account_info.__func__(StorageAsyncClient, info, *args, **kwargs)  # type: ignore

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
            StorageAsyncClient: The constructed client.
        """
        return StorageClient.from_service_account_file.__func__(StorageAsyncClient, filename, *args, **kwargs)  # type: ignore

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
        return StorageClient.get_mtls_endpoint_and_cert_source(client_options)  # type: ignore

    @property
    def transport(self) -> StorageTransport:
        """Returns the transport used by the client instance.

        Returns:
            StorageTransport: The transport used by the client instance.
        """
        return self._client.transport

    get_transport_class = functools.partial(type(StorageClient).get_transport_class, type(StorageClient))

    def __init__(self, *,
            credentials: Optional[ga_credentials.Credentials] = None,
            transport: Union[str, StorageTransport] = "grpc_asyncio",
            client_options: Optional[ClientOptions] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            ) -> None:
        """Instantiates the storage client.

        Args:
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
            transport (Union[str, ~.StorageTransport]): The
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
        self._client = StorageClient(
            credentials=credentials,
            transport=transport,
            client_options=client_options,
            client_info=client_info,

        )

    async def delete_bucket(self,
            request: Optional[Union[storage.DeleteBucketRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Permanently deletes an empty bucket.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_delete_bucket():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.DeleteBucketRequest(
                    name="name_value",
                )

                # Make the request
                await client.delete_bucket(request=request)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.DeleteBucketRequest, dict]]):
                The request object. Request message for DeleteBucket.
            name (:class:`str`):
                Required. Name of a bucket to delete.
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

        request = storage.DeleteBucketRequest(request)

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

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def get_bucket(self,
            request: Optional[Union[storage.GetBucketRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.Bucket:
        r"""Returns metadata for the specified bucket.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_get_bucket():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.GetBucketRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.get_bucket(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.GetBucketRequest, dict]]):
                The request object. Request message for GetBucket.
            name (:class:`str`):
                Required. Name of a bucket.
                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket:
                A bucket.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.GetBucketRequest(request)

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

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def create_bucket(self,
            request: Optional[Union[storage.CreateBucketRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            bucket: Optional[storage.Bucket] = None,
            bucket_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.Bucket:
        r"""Creates a new bucket.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_create_bucket():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.CreateBucketRequest(
                    parent="parent_value",
                    bucket_id="bucket_id_value",
                )

                # Make the request
                response = await client.create_bucket(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CreateBucketRequest, dict]]):
                The request object. Request message for CreateBucket.
            parent (:class:`str`):
                Required. The project to which this
                bucket will belong.

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket (:class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket`):
                Properties of the new bucket being inserted. The name of
                the bucket is specified in the ``bucket_id`` field.
                Populating ``bucket.name`` field will result in an
                error. The project of the bucket must be specified in
                the ``bucket.project`` field. This field must be in
                ``projects/{projectIdentifier}`` format,
                {projectIdentifier} can be the project ID or project
                number. The ``parent`` field must be either empty or
                ``projects/_``.

                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            bucket_id (:class:`str`):
                Required. The ID to use for this bucket, which will
                become the final component of the bucket's resource
                name. For example, the value ``foo`` might result in a
                bucket with the name ``projects/123456/buckets/foo``.

                This corresponds to the ``bucket_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket:
                A bucket.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent, bucket, bucket_id])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.CreateBucketRequest(request)

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

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def list_buckets(self,
            request: Optional[Union[storage.ListBucketsRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListBucketsAsyncPager:
        r"""Retrieves a list of buckets for a given project.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_list_buckets():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.ListBucketsRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_buckets(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListBucketsRequest, dict]]):
                The request object. Request message for ListBuckets.
            parent (:class:`str`):
                Required. The project whose buckets
                we are listing.

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.services.storage.pagers.ListBucketsAsyncPager:
                The result of a call to
                Buckets.ListBuckets
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

        request = storage.ListBucketsRequest(request)

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

    async def lock_bucket_retention_policy(self,
            request: Optional[Union[storage.LockBucketRetentionPolicyRequest, dict]] = None,
            *,
            bucket: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.Bucket:
        r"""Locks retention policy on a bucket.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_lock_bucket_retention_policy():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.LockBucketRetentionPolicyRequest(
                    bucket="bucket_value",
                    if_metageneration_match=2413,
                )

                # Make the request
                response = await client.lock_bucket_retention_policy(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.LockBucketRetentionPolicyRequest, dict]]):
                The request object. Request message for
                LockBucketRetentionPolicyRequest.
            bucket (:class:`str`):
                Required. Name of a bucket.
                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket:
                A bucket.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([bucket])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.LockBucketRetentionPolicyRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if bucket is not None:
            request.bucket = bucket

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.lock_bucket_retention_policy,
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

        # Done; return the response.
        return response

    async def get_iam_policy(self,
            request: Optional[Union[iam_policy_pb2.GetIamPolicyRequest, dict]] = None,
            *,
            resource: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> policy_pb2.Policy:
        r"""Gets the IAM policy for a specified bucket. The ``resource``
        field in the request should be ``projects/_/buckets/{bucket}``.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google.iam.v1 import iam_policy_pb2  # type: ignore
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_get_iam_policy():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = iam_policy_pb2.GetIamPolicyRequest(
                    resource="resource_value",
                )

                # Make the request
                response = await client.get_iam_policy(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.iam.v1.iam_policy_pb2.GetIamPolicyRequest, dict]]):
                The request object. Request message for ``GetIamPolicy`` method.
            resource (:class:`str`):
                REQUIRED: The resource for which the
                policy is being requested. See the
                operation documentation for the
                appropriate value for this field.

                This corresponds to the ``resource`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.iam.v1.policy_pb2.Policy:
                Defines an Identity and Access Management (IAM) policy. It is used to
                   specify access control policies for Cloud Platform
                   resources.

                   A Policy is a collection of bindings. A binding binds
                   one or more members to a single role. Members can be
                   user accounts, service accounts, Google groups, and
                   domains (such as G Suite). A role is a named list of
                   permissions (defined by IAM or configured by users).
                   A binding can optionally specify a condition, which
                   is a logic expression that further constrains the
                   role binding based on attributes about the request
                   and/or target resource.

                   **JSON Example**

                      {
                         "bindings": [
                            {
                               "role":
                               "roles/resourcemanager.organizationAdmin",
                               "members": [ "user:mike@example.com",
                               "group:admins@example.com",
                               "domain:google.com",
                               "serviceAccount:my-project-id@appspot.gserviceaccount.com"
                               ]

                            }, { "role":
                            "roles/resourcemanager.organizationViewer",
                            "members": ["user:eve@example.com"],
                            "condition": { "title": "expirable access",
                            "description": "Does not grant access after
                            Sep 2020", "expression": "request.time <
                            timestamp('2020-10-01T00:00:00.000Z')", } }

                         ]

                      }

                   **YAML Example**

                      bindings: - members: - user:\ mike@example.com -
                      group:\ admins@example.com - domain:google.com -
                      serviceAccount:\ my-project-id@appspot.gserviceaccount.com
                      role: roles/resourcemanager.organizationAdmin -
                      members: - user:\ eve@example.com role:
                      roles/resourcemanager.organizationViewer
                      condition: title: expirable access description:
                      Does not grant access after Sep 2020 expression:
                      request.time <
                      timestamp('2020-10-01T00:00:00.000Z')

                   For a description of IAM and its features, see the
                   [IAM developer's
                   guide](\ https://cloud.google.com/iam/docs).

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([resource])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

         # The request isn't a proto-plus wrapped type,
        # so it must be constructed via keyword expansion.
        if isinstance(request, dict):
            request = iam_policy_pb2.GetIamPolicyRequest(**request)
        elif not request:
            request = iam_policy_pb2.GetIamPolicyRequest(resource=resource, )

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_iam_policy,
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

        # Done; return the response.
        return response

    async def set_iam_policy(self,
            request: Optional[Union[iam_policy_pb2.SetIamPolicyRequest, dict]] = None,
            *,
            resource: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> policy_pb2.Policy:
        r"""Updates an IAM policy for the specified bucket. The ``resource``
        field in the request should be ``projects/_/buckets/{bucket}``.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google.iam.v1 import iam_policy_pb2  # type: ignore
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_set_iam_policy():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = iam_policy_pb2.SetIamPolicyRequest(
                    resource="resource_value",
                )

                # Make the request
                response = await client.set_iam_policy(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.iam.v1.iam_policy_pb2.SetIamPolicyRequest, dict]]):
                The request object. Request message for ``SetIamPolicy`` method.
            resource (:class:`str`):
                REQUIRED: The resource for which the
                policy is being specified. See the
                operation documentation for the
                appropriate value for this field.

                This corresponds to the ``resource`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.iam.v1.policy_pb2.Policy:
                Defines an Identity and Access Management (IAM) policy. It is used to
                   specify access control policies for Cloud Platform
                   resources.

                   A Policy is a collection of bindings. A binding binds
                   one or more members to a single role. Members can be
                   user accounts, service accounts, Google groups, and
                   domains (such as G Suite). A role is a named list of
                   permissions (defined by IAM or configured by users).
                   A binding can optionally specify a condition, which
                   is a logic expression that further constrains the
                   role binding based on attributes about the request
                   and/or target resource.

                   **JSON Example**

                      {
                         "bindings": [
                            {
                               "role":
                               "roles/resourcemanager.organizationAdmin",
                               "members": [ "user:mike@example.com",
                               "group:admins@example.com",
                               "domain:google.com",
                               "serviceAccount:my-project-id@appspot.gserviceaccount.com"
                               ]

                            }, { "role":
                            "roles/resourcemanager.organizationViewer",
                            "members": ["user:eve@example.com"],
                            "condition": { "title": "expirable access",
                            "description": "Does not grant access after
                            Sep 2020", "expression": "request.time <
                            timestamp('2020-10-01T00:00:00.000Z')", } }

                         ]

                      }

                   **YAML Example**

                      bindings: - members: - user:\ mike@example.com -
                      group:\ admins@example.com - domain:google.com -
                      serviceAccount:\ my-project-id@appspot.gserviceaccount.com
                      role: roles/resourcemanager.organizationAdmin -
                      members: - user:\ eve@example.com role:
                      roles/resourcemanager.organizationViewer
                      condition: title: expirable access description:
                      Does not grant access after Sep 2020 expression:
                      request.time <
                      timestamp('2020-10-01T00:00:00.000Z')

                   For a description of IAM and its features, see the
                   [IAM developer's
                   guide](\ https://cloud.google.com/iam/docs).

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([resource])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

         # The request isn't a proto-plus wrapped type,
        # so it must be constructed via keyword expansion.
        if isinstance(request, dict):
            request = iam_policy_pb2.SetIamPolicyRequest(**request)
        elif not request:
            request = iam_policy_pb2.SetIamPolicyRequest(resource=resource, )

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.set_iam_policy,
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

        # Done; return the response.
        return response

    async def test_iam_permissions(self,
            request: Optional[Union[iam_policy_pb2.TestIamPermissionsRequest, dict]] = None,
            *,
            resource: Optional[str] = None,
            permissions: Optional[MutableSequence[str]] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> iam_policy_pb2.TestIamPermissionsResponse:
        r"""Tests a set of permissions on the given bucket or object to see
        which, if any, are held by the caller. The ``resource`` field in
        the request should be ``projects/_/buckets/{bucket}`` for a
        bucket or ``projects/_/buckets/{bucket}/objects/{object}`` for
        an object.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from google.iam.v1 import iam_policy_pb2  # type: ignore
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_test_iam_permissions():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = iam_policy_pb2.TestIamPermissionsRequest(
                    resource="resource_value",
                    permissions=['permissions_value1', 'permissions_value2'],
                )

                # Make the request
                response = await client.test_iam_permissions(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[google.iam.v1.iam_policy_pb2.TestIamPermissionsRequest, dict]]):
                The request object. Request message for ``TestIamPermissions`` method.
            resource (:class:`str`):
                REQUIRED: The resource for which the
                policy detail is being requested. See
                the operation documentation for the
                appropriate value for this field.

                This corresponds to the ``resource`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            permissions (:class:`MutableSequence[str]`):
                The set of permissions to check for the ``resource``.
                Permissions with wildcards (such as '*' or 'storage.*')
                are not allowed. For more information see `IAM
                Overview <https://cloud.google.com/iam/docs/overview#permissions>`__.

                This corresponds to the ``permissions`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            google.iam.v1.iam_policy_pb2.TestIamPermissionsResponse:
                Response message for TestIamPermissions method.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([resource, permissions])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

         # The request isn't a proto-plus wrapped type,
        # so it must be constructed via keyword expansion.
        if isinstance(request, dict):
            request = iam_policy_pb2.TestIamPermissionsRequest(**request)
        elif not request:
            request = iam_policy_pb2.TestIamPermissionsRequest(resource=resource, permissions=permissions, )

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.test_iam_permissions,
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

        # Done; return the response.
        return response

    async def update_bucket(self,
            request: Optional[Union[storage.UpdateBucketRequest, dict]] = None,
            *,
            bucket: Optional[storage.Bucket] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.Bucket:
        r"""Updates a bucket. Equivalent to JSON API's
        storage.buckets.patch method.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_update_bucket():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.UpdateBucketRequest(
                )

                # Make the request
                response = await client.update_bucket(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.UpdateBucketRequest, dict]]):
                The request object. Request for UpdateBucket method.
            bucket (:class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket`):
                Required. The bucket to update. The bucket's ``name``
                field will be used to identify the bucket.

                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
                Required. List of fields to be updated.

                To specify ALL fields, equivalent to the JSON API's
                "update" function, specify a single field with the value
                ``*``. Note: not recommended. If a new field is
                introduced at a later time, an older client updating
                with the ``*`` may accidentally reset the new field's
                value.

                Not specifying any fields is an error.

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket:
                A bucket.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([bucket, update_mask])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.UpdateBucketRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
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

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def compose_object(self,
            request: Optional[Union[storage.ComposeObjectRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.Object:
        r"""Concatenates a list of existing objects into a new
        object in the same bucket.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_compose_object():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.ComposeObjectRequest(
                )

                # Make the request
                response = await client.compose_object(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ComposeObjectRequest, dict]]):
                The request object. Request message for ComposeObject.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object:
                An object.
        """
        # Create or coerce a protobuf request object.
        request = storage.ComposeObjectRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.compose_object,
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

        # Done; return the response.
        return response

    async def delete_object(self,
            request: Optional[Union[storage.DeleteObjectRequest, dict]] = None,
            *,
            bucket: Optional[str] = None,
            object_: Optional[str] = None,
            generation: Optional[int] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Deletes an object and its metadata.

        Deletions are normally permanent when versioning is
        disabled or whenever the generation parameter is used.
        However, if soft delete is enabled for the bucket,
        deleted objects can be restored using RestoreObject
        until the soft delete retention period has passed.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_delete_object():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.DeleteObjectRequest(
                    bucket="bucket_value",
                    object_="object__value",
                )

                # Make the request
                await client.delete_object(request=request)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.DeleteObjectRequest, dict]]):
                The request object. Message for deleting an object. ``bucket`` and
                ``object`` **must** be set.
            bucket (:class:`str`):
                Required. Name of the bucket in which
                the object resides.

                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            object_ (:class:`str`):
                Required. The name of the finalized object to delete.
                Note: If you want to delete an unfinalized resumable
                upload please use ``CancelResumableWrite``.

                This corresponds to the ``object_`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            generation (:class:`int`):
                If present, permanently deletes a
                specific revision of this object (as
                opposed to the latest version, the
                default).

                This corresponds to the ``generation`` field
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
        has_flattened_params = any([bucket, object_, generation])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.DeleteObjectRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if bucket is not None:
            request.bucket = bucket
        if object_ is not None:
            request.object_ = object_
        if generation is not None:
            request.generation = generation

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_object,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def restore_object(self,
            request: Optional[Union[storage.RestoreObjectRequest, dict]] = None,
            *,
            bucket: Optional[str] = None,
            object_: Optional[str] = None,
            generation: Optional[int] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.Object:
        r"""Restores a soft-deleted object.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_restore_object():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.RestoreObjectRequest(
                    bucket="bucket_value",
                    object_="object__value",
                    generation=1068,
                )

                # Make the request
                response = await client.restore_object(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.RestoreObjectRequest, dict]]):
                The request object. Message for restoring an object. ``bucket``, ``object``,
                and ``generation`` **must** be set.
            bucket (:class:`str`):
                Required. Name of the bucket in which
                the object resides.

                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            object_ (:class:`str`):
                Required. The name of the object to
                restore.

                This corresponds to the ``object_`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            generation (:class:`int`):
                Required. The specific revision of
                the object to restore.

                This corresponds to the ``generation`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object:
                An object.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([bucket, object_, generation])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.RestoreObjectRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if bucket is not None:
            request.bucket = bucket
        if object_ is not None:
            request.object_ = object_
        if generation is not None:
            request.generation = generation

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.restore_object,
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

        # Done; return the response.
        return response

    async def cancel_resumable_write(self,
            request: Optional[Union[storage.CancelResumableWriteRequest, dict]] = None,
            *,
            upload_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.CancelResumableWriteResponse:
        r"""Cancels an in-progress resumable upload.

        Any attempts to write to the resumable upload after
        cancelling the upload will fail.

        The behavior for currently in progress write operations
        is not guaranteed - they could either complete before
        the cancellation or fail if the cancellation completes
        first.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_cancel_resumable_write():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.CancelResumableWriteRequest(
                    upload_id="upload_id_value",
                )

                # Make the request
                response = await client.cancel_resumable_write(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CancelResumableWriteRequest, dict]]):
                The request object. Message for canceling an in-progress resumable upload.
                ``upload_id`` **must** be set.
            upload_id (:class:`str`):
                Required. The upload_id of the resumable upload to
                cancel. This should be copied from the ``upload_id``
                field of ``StartResumableWriteResponse``.

                This corresponds to the ``upload_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CancelResumableWriteResponse:
                Empty response message for canceling
                an in-progress resumable upload, will be
                extended as needed.

        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([upload_id])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.CancelResumableWriteRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if upload_id is not None:
            request.upload_id = upload_id

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.cancel_resumable_write,
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

        # Done; return the response.
        return response

    async def get_object(self,
            request: Optional[Union[storage.GetObjectRequest, dict]] = None,
            *,
            bucket: Optional[str] = None,
            object_: Optional[str] = None,
            generation: Optional[int] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.Object:
        r"""Retrieves an object's metadata.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_get_object():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.GetObjectRequest(
                    bucket="bucket_value",
                    object_="object__value",
                )

                # Make the request
                response = await client.get_object(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.GetObjectRequest, dict]]):
                The request object. Request message for GetObject.
            bucket (:class:`str`):
                Required. Name of the bucket in which
                the object resides.

                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            object_ (:class:`str`):
                Required. Name of the object.
                This corresponds to the ``object_`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            generation (:class:`int`):
                If present, selects a specific
                revision of this object (as opposed to
                the latest version, the default).

                This corresponds to the ``generation`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object:
                An object.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([bucket, object_, generation])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.GetObjectRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if bucket is not None:
            request.bucket = bucket
        if object_ is not None:
            request.object_ = object_
        if generation is not None:
            request.generation = generation

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_object,
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

        # Done; return the response.
        return response

    def read_object(self,
            request: Optional[Union[storage.ReadObjectRequest, dict]] = None,
            *,
            bucket: Optional[str] = None,
            object_: Optional[str] = None,
            generation: Optional[int] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> Awaitable[AsyncIterable[storage.ReadObjectResponse]]:
        r"""Reads an object's data.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_read_object():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.ReadObjectRequest(
                    bucket="bucket_value",
                    object_="object__value",
                )

                # Make the request
                stream = await client.read_object(request=request)

                # Handle the response
                async for response in stream:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ReadObjectRequest, dict]]):
                The request object. Request message for ReadObject.
            bucket (:class:`str`):
                Required. The name of the bucket
                containing the object to read.

                This corresponds to the ``bucket`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            object_ (:class:`str`):
                Required. The name of the object to
                read.

                This corresponds to the ``object_`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            generation (:class:`int`):
                If present, selects a specific
                revision of this object (as opposed to
                the latest version, the default).

                This corresponds to the ``generation`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            AsyncIterable[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ReadObjectResponse]:
                Response message for ReadObject.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([bucket, object_, generation])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.ReadObjectRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if bucket is not None:
            request.bucket = bucket
        if object_ is not None:
            request.object_ = object_
        if generation is not None:
            request.generation = generation

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.read_object,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
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

    async def update_object(self,
            request: Optional[Union[storage.UpdateObjectRequest, dict]] = None,
            *,
            object_: Optional[storage.Object] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.Object:
        r"""Updates an object's metadata.
        Equivalent to JSON API's storage.objects.patch.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_update_object():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.UpdateObjectRequest(
                )

                # Make the request
                response = await client.update_object(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.UpdateObjectRequest, dict]]):
                The request object. Request message for UpdateObject.
            object_ (:class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object`):
                Required. The object to update.
                The object's bucket and name fields are
                used to identify the object to update.
                If present, the object's generation
                field selects a specific revision of
                this object whose metadata should be
                updated. Otherwise, assumes the live
                version of the object.

                This corresponds to the ``object_`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
                Required. List of fields to be updated.

                To specify ALL fields, equivalent to the JSON API's
                "update" function, specify a single field with the value
                ``*``. Note: not recommended. If a new field is
                introduced at a later time, an older client updating
                with the ``*`` may accidentally reset the new field's
                value.

                Not specifying any fields is an error.

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object:
                An object.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([object_, update_mask])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.UpdateObjectRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if object_ is not None:
            request.object_ = object_
        if update_mask is not None:
            request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_object,
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

        # Done; return the response.
        return response

    async def write_object(self,
            requests: Optional[AsyncIterator[storage.WriteObjectRequest]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.WriteObjectResponse:
        r"""Stores a new object and metadata.

        An object can be written either in a single message stream or in
        a resumable sequence of message streams. To write using a single
        stream, the client should include in the first message of the
        stream an ``WriteObjectSpec`` describing the destination bucket,
        object, and any preconditions. Additionally, the final message
        must set 'finish_write' to true, or else it is an error.

        For a resumable write, the client should instead call
        ``StartResumableWrite()``, populating a ``WriteObjectSpec`` into
        that request. They should then attach the returned ``upload_id``
        to the first message of each following call to ``WriteObject``.
        If the stream is closed before finishing the upload (either
        explicitly by the client or due to a network error or an error
        response from the server), the client should do as follows:

        -  Check the result Status of the stream, to determine if
           writing can be resumed on this stream or must be restarted
           from scratch (by calling ``StartResumableWrite()``). The
           resumable errors are DEADLINE_EXCEEDED, INTERNAL, and
           UNAVAILABLE. For each case, the client should use binary
           exponential backoff before retrying. Additionally, writes can
           be resumed after RESOURCE_EXHAUSTED errors, but only after
           taking appropriate measures, which may include reducing
           aggregate send rate across clients and/or requesting a quota
           increase for your project.
        -  If the call to ``WriteObject`` returns ``ABORTED``, that
           indicates concurrent attempts to update the resumable write,
           caused either by multiple racing clients or by a single
           client where the previous request was timed out on the client
           side but nonetheless reached the server. In this case the
           client should take steps to prevent further concurrent writes
           (e.g., increase the timeouts, stop using more than one
           process to perform the upload, etc.), and then should follow
           the steps below for resuming the upload.
        -  For resumable errors, the client should call
           ``QueryWriteStatus()`` and then continue writing from the
           returned ``persisted_size``. This may be less than the amount
           of data the client previously sent. Note also that it is
           acceptable to send data starting at an offset earlier than
           the returned ``persisted_size``; in this case, the service
           will skip data at offsets that were already persisted
           (without checking that it matches the previously written
           data), and write only the data starting from the persisted
           offset. Even though the data isn't written, it may still
           incur a performance cost over resuming at the correct write
           offset. This behavior can make client-side handling simpler
           in some cases.
        -  Clients must only send data that is a multiple of 256 KiB per
           message, unless the object is being finished with
           ``finish_write`` set to ``true``.

        The service will not view the object as complete until the
        client has sent a ``WriteObjectRequest`` with ``finish_write``
        set to ``true``. Sending any requests on a stream after sending
        a request with ``finish_write`` set to ``true`` will cause an
        error. The client **should** check the response it receives to
        determine how much data the service was able to commit and
        whether the service views the object as complete.

        Attempting to resume an already finalized object will result in
        an OK status, with a WriteObjectResponse containing the
        finalized object's metadata.

        Alternatively, the BidiWriteObject operation may be used to
        write an object with controls over flushing and the ability to
        fetch the ability to determine the current persisted size.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_write_object():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.WriteObjectRequest(
                    upload_id="upload_id_value",
                    write_offset=1297,
                )

                # This method expects an iterator which contains
                # 'storage_v2.WriteObjectRequest' objects
                # Here we create a generator that yields a single `request` for
                # demonstrative purposes.
                requests = [request]

                def request_generator():
                    for request in requests:
                        yield request

                # Make the request
                response = await client.write_object(requests=request_generator())

                # Handle the response
                print(response)

        Args:
            requests (AsyncIterator[`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.WriteObjectRequest`]):
                The request object AsyncIterator. Request message for WriteObject.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.WriteObjectResponse:
                Response message for WriteObject.
        """

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.write_object,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Send the request.
        response = await rpc(
            requests,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    def bidi_write_object(self,
            requests: Optional[AsyncIterator[storage.BidiWriteObjectRequest]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> Awaitable[AsyncIterable[storage.BidiWriteObjectResponse]]:
        r"""Stores a new object and metadata.

        This is similar to the WriteObject call with the added support
        for manual flushing of persisted state, and the ability to
        determine current persisted size without closing the stream.

        The client may specify one or both of the ``state_lookup`` and
        ``flush`` fields in each BidiWriteObjectRequest. If ``flush`` is
        specified, the data written so far will be persisted to storage.
        If ``state_lookup`` is specified, the service will respond with
        a BidiWriteObjectResponse that contains the persisted size. If
        both ``flush`` and ``state_lookup`` are specified, the flush
        will always occur before a ``state_lookup``, so that both may be
        set in the same request and the returned state will be the state
        of the object post-flush. When the stream is closed, a
        BidiWriteObjectResponse will always be sent to the client,
        regardless of the value of ``state_lookup``.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_bidi_write_object():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.BidiWriteObjectRequest(
                    upload_id="upload_id_value",
                    write_offset=1297,
                )

                # This method expects an iterator which contains
                # 'storage_v2.BidiWriteObjectRequest' objects
                # Here we create a generator that yields a single `request` for
                # demonstrative purposes.
                requests = [request]

                def request_generator():
                    for request in requests:
                        yield request

                # Make the request
                stream = await client.bidi_write_object(requests=request_generator())

                # Handle the response
                async for response in stream:
                    print(response)

        Args:
            requests (AsyncIterator[`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.BidiWriteObjectRequest`]):
                The request object AsyncIterator. Request message for BidiWriteObject.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            AsyncIterable[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.BidiWriteObjectResponse]:
                Response message for BidiWriteObject.
        """

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.bidi_write_object,
            default_timeout=None,
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

    async def list_objects(self,
            request: Optional[Union[storage.ListObjectsRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListObjectsAsyncPager:
        r"""Retrieves a list of objects matching the criteria.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_list_objects():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.ListObjectsRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_objects(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListObjectsRequest, dict]]):
                The request object. Request message for ListObjects.
            parent (:class:`str`):
                Required. Name of the bucket in which
                to look for objects.

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.services.storage.pagers.ListObjectsAsyncPager:
                The result of a call to
                Objects.ListObjects
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

        request = storage.ListObjectsRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_objects,
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

        # This method is paged; wrap the response in a pager, which provides
        # an `__aiter__` convenience method.
        response = pagers.ListObjectsAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def rewrite_object(self,
            request: Optional[Union[storage.RewriteObjectRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.RewriteResponse:
        r"""Rewrites a source object to a destination object.
        Optionally overrides metadata.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_rewrite_object():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.RewriteObjectRequest(
                    destination_name="destination_name_value",
                    destination_bucket="destination_bucket_value",
                    source_bucket="source_bucket_value",
                    source_object="source_object_value",
                )

                # Make the request
                response = await client.rewrite_object(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.RewriteObjectRequest, dict]]):
                The request object. Request message for RewriteObject. If the source object
                is encrypted using a Customer-Supplied Encryption Key
                the key information must be provided in the
                copy_source_encryption_algorithm,
                copy_source_encryption_key_bytes, and
                copy_source_encryption_key_sha256_bytes fields. If the
                destination object should be encrypted the keying
                information should be provided in the
                encryption_algorithm, encryption_key_bytes, and
                encryption_key_sha256_bytes fields of the
                common_object_request_params.customer_encryption field.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.RewriteResponse:
                A rewrite response.
        """
        # Create or coerce a protobuf request object.
        request = storage.RewriteObjectRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.rewrite_object,
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

        # Done; return the response.
        return response

    async def start_resumable_write(self,
            request: Optional[Union[storage.StartResumableWriteRequest, dict]] = None,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.StartResumableWriteResponse:
        r"""Starts a resumable write. How long the write
        operation remains valid, and what happens when the write
        operation becomes invalid, are service-dependent.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_start_resumable_write():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.StartResumableWriteRequest(
                )

                # Make the request
                response = await client.start_resumable_write(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.StartResumableWriteRequest, dict]]):
                The request object. Request message StartResumableWrite.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.StartResumableWriteResponse:
                Response object for StartResumableWrite.
        """
        # Create or coerce a protobuf request object.
        request = storage.StartResumableWriteRequest(request)

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.start_resumable_write,
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

        # Done; return the response.
        return response

    async def query_write_status(self,
            request: Optional[Union[storage.QueryWriteStatusRequest, dict]] = None,
            *,
            upload_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.QueryWriteStatusResponse:
        r"""Determines the ``persisted_size`` for an object that is being
        written, which can then be used as the ``write_offset`` for the
        next ``Write()`` call.

        If the object does not exist (i.e., the object has been deleted,
        or the first ``Write()`` has not yet reached the service), this
        method returns the error ``NOT_FOUND``.

        The client **may** call ``QueryWriteStatus()`` at any time to
        determine how much data has been processed for this object. This
        is useful if the client is buffering data and needs to know
        which data can be safely evicted. For any sequence of
        ``QueryWriteStatus()`` calls for a given object name, the
        sequence of returned ``persisted_size`` values will be
        non-decreasing.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_query_write_status():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.QueryWriteStatusRequest(
                    upload_id="upload_id_value",
                )

                # Make the request
                response = await client.query_write_status(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.QueryWriteStatusRequest, dict]]):
                The request object. Request object for ``QueryWriteStatus``.
            upload_id (:class:`str`):
                Required. The name of the resume
                token for the object whose write status
                is being requested.

                This corresponds to the ``upload_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.QueryWriteStatusResponse:
                Response object for QueryWriteStatus.
        """
        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([upload_id])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.QueryWriteStatusRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if upload_id is not None:
            request.upload_id = upload_id

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.query_write_status,
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

        # Done; return the response.
        return response

    async def get_service_account(self,
            request: Optional[Union[storage.GetServiceAccountRequest, dict]] = None,
            *,
            project: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.ServiceAccount:
        r"""Retrieves the name of a project's Google Cloud
        Storage service account.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_get_service_account():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.GetServiceAccountRequest(
                    project="project_value",
                )

                # Make the request
                response = await client.get_service_account(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.GetServiceAccountRequest, dict]]):
                The request object. Request message for
                GetServiceAccount.
            project (:class:`str`):
                Required. Project ID, in the format
                of "projects/{projectIdentifier}".
                {projectIdentifier} can be the project
                ID or project number.

                This corresponds to the ``project`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ServiceAccount:
                A service account, owned by Cloud
                Storage, which may be used when taking
                action on behalf of a given project, for
                example to publish Pub/Sub notifications
                or to retrieve security keys.

        """
        warnings.warn("StorageAsyncClient.get_service_account is deprecated",
            DeprecationWarning)

        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([project])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.GetServiceAccountRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if project is not None:
            request.project = project

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_service_account,
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

        # Done; return the response.
        return response

    async def create_hmac_key(self,
            request: Optional[Union[storage.CreateHmacKeyRequest, dict]] = None,
            *,
            project: Optional[str] = None,
            service_account_email: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.CreateHmacKeyResponse:
        r"""Creates a new HMAC key for the given service account.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_create_hmac_key():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.CreateHmacKeyRequest(
                    project="project_value",
                    service_account_email="service_account_email_value",
                )

                # Make the request
                response = await client.create_hmac_key(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CreateHmacKeyRequest, dict]]):
                The request object. Request message for CreateHmacKey.
            project (:class:`str`):
                Required. The project that the
                HMAC-owning service account lives in, in
                the format of
                "projects/{projectIdentifier}".
                {projectIdentifier} can be the project
                ID or project number.

                This corresponds to the ``project`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            service_account_email (:class:`str`):
                Required. The service account to
                create the HMAC for.

                This corresponds to the ``service_account_email`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CreateHmacKeyResponse:
                Create hmac response.  The only time
                the secret for an HMAC will be returned.

        """
        warnings.warn("StorageAsyncClient.create_hmac_key is deprecated",
            DeprecationWarning)

        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([project, service_account_email])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.CreateHmacKeyRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if project is not None:
            request.project = project
        if service_account_email is not None:
            request.service_account_email = service_account_email

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_hmac_key,
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

        # Done; return the response.
        return response

    async def delete_hmac_key(self,
            request: Optional[Union[storage.DeleteHmacKeyRequest, dict]] = None,
            *,
            access_id: Optional[str] = None,
            project: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Deletes a given HMAC key.  Key must be in an INACTIVE
        state.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_delete_hmac_key():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.DeleteHmacKeyRequest(
                    access_id="access_id_value",
                    project="project_value",
                )

                # Make the request
                await client.delete_hmac_key(request=request)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.DeleteHmacKeyRequest, dict]]):
                The request object. Request object to delete a given HMAC
                key.
            access_id (:class:`str`):
                Required. The identifying key for the
                HMAC to delete.

                This corresponds to the ``access_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            project (:class:`str`):
                Required. The project that owns the
                HMAC key, in the format of
                "projects/{projectIdentifier}".
                {projectIdentifier} can be the project
                ID or project number.

                This corresponds to the ``project`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        warnings.warn("StorageAsyncClient.delete_hmac_key is deprecated",
            DeprecationWarning)

        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([access_id, project])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.DeleteHmacKeyRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if access_id is not None:
            request.access_id = access_id
        if project is not None:
            request.project = project

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_hmac_key,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def get_hmac_key(self,
            request: Optional[Union[storage.GetHmacKeyRequest, dict]] = None,
            *,
            access_id: Optional[str] = None,
            project: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.HmacKeyMetadata:
        r"""Gets an existing HMAC key metadata for the given id.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_get_hmac_key():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.GetHmacKeyRequest(
                    access_id="access_id_value",
                    project="project_value",
                )

                # Make the request
                response = await client.get_hmac_key(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.GetHmacKeyRequest, dict]]):
                The request object. Request object to get metadata on a
                given HMAC key.
            access_id (:class:`str`):
                Required. The identifying key for the
                HMAC to delete.

                This corresponds to the ``access_id`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            project (:class:`str`):
                Required. The project the HMAC key
                lies in, in the format of
                "projects/{projectIdentifier}".
                {projectIdentifier} can be the project
                ID or project number.

                This corresponds to the ``project`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.HmacKeyMetadata:
                Hmac Key Metadata, which includes all
                information other than the secret.

        """
        warnings.warn("StorageAsyncClient.get_hmac_key is deprecated",
            DeprecationWarning)

        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([access_id, project])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.GetHmacKeyRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if access_id is not None:
            request.access_id = access_id
        if project is not None:
            request.project = project

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_hmac_key,
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

        # Done; return the response.
        return response

    async def list_hmac_keys(self,
            request: Optional[Union[storage.ListHmacKeysRequest, dict]] = None,
            *,
            project: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListHmacKeysAsyncPager:
        r"""Lists HMAC keys under a given project with the
        additional filters provided.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_list_hmac_keys():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.ListHmacKeysRequest(
                    project="project_value",
                )

                # Make the request
                page_result = client.list_hmac_keys(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListHmacKeysRequest, dict]]):
                The request object. Request to fetch a list of HMAC keys
                under a given project.
            project (:class:`str`):
                Required. The project to list HMAC
                keys for, in the format of
                "projects/{projectIdentifier}".
                {projectIdentifier} can be the project
                ID or project number.

                This corresponds to the ``project`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.services.storage.pagers.ListHmacKeysAsyncPager:
                Hmac key list response with next page
                information.
                Iterating over this object will yield
                results and resolve additional pages
                automatically.

        """
        warnings.warn("StorageAsyncClient.list_hmac_keys is deprecated",
            DeprecationWarning)

        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([project])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.ListHmacKeysRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if project is not None:
            request.project = project

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_hmac_keys,
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

        # This method is paged; wrap the response in a pager, which provides
        # an `__aiter__` convenience method.
        response = pagers.ListHmacKeysAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def update_hmac_key(self,
            request: Optional[Union[storage.UpdateHmacKeyRequest, dict]] = None,
            *,
            hmac_key: Optional[storage.HmacKeyMetadata] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.HmacKeyMetadata:
        r"""Updates a given HMAC key state between ACTIVE and
        INACTIVE.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_update_hmac_key():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.UpdateHmacKeyRequest(
                )

                # Make the request
                response = await client.update_hmac_key(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.UpdateHmacKeyRequest, dict]]):
                The request object. Request object to update an HMAC key
                state. HmacKeyMetadata.state is required
                and the only writable field in
                UpdateHmacKey operation. Specifying
                fields other than state will result in
                an error.
            hmac_key (:class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.HmacKeyMetadata`):
                Required. The HMAC key to update. If present, the
                hmac_key's ``id`` field will be used to identify the
                key. Otherwise, the hmac_key's access_id and project
                fields will be used to identify the key.

                This corresponds to the ``hmac_key`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
                Update mask for hmac_key. Not specifying any fields will
                mean only the ``state`` field is updated to the value
                specified in ``hmac_key``.

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.HmacKeyMetadata:
                Hmac Key Metadata, which includes all
                information other than the secret.

        """
        warnings.warn("StorageAsyncClient.update_hmac_key is deprecated",
            DeprecationWarning)

        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([hmac_key, update_mask])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.UpdateHmacKeyRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if hmac_key is not None:
            request.hmac_key = hmac_key
        if update_mask is not None:
            request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.update_hmac_key,
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

        # Done; return the response.
        return response

    async def delete_notification_config(self,
            request: Optional[Union[storage.DeleteNotificationConfigRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> None:
        r"""Permanently deletes a NotificationConfig.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_delete_notification_config():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.DeleteNotificationConfigRequest(
                    name="name_value",
                )

                # Make the request
                await client.delete_notification_config(request=request)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.DeleteNotificationConfigRequest, dict]]):
                The request object. Request message for
                DeleteNotificationConfig.
            name (:class:`str`):
                Required. The parent bucket of the
                NotificationConfig.

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.
        """
        warnings.warn("StorageAsyncClient.delete_notification_config is deprecated",
            DeprecationWarning)

        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.DeleteNotificationConfigRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.delete_notification_config,
            default_timeout=None,
            client_info=DEFAULT_CLIENT_INFO,
        )

        # Send the request.
        await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

    async def get_notification_config(self,
            request: Optional[Union[storage.GetNotificationConfigRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.NotificationConfig:
        r"""View a NotificationConfig.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_get_notification_config():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.GetNotificationConfigRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.get_notification_config(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.GetNotificationConfigRequest, dict]]):
                The request object. Request message for
                GetNotificationConfig.
            name (:class:`str`):
                Required. The parent bucket of the NotificationConfig.
                Format:
                ``projects/{project}/buckets/{bucket}/notificationConfigs/{notificationConfig}``

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.NotificationConfig:
                A directive to publish Pub/Sub
                notifications upon changes to a bucket.

        """
        warnings.warn("StorageAsyncClient.get_notification_config is deprecated",
            DeprecationWarning)

        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([name])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.GetNotificationConfigRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.get_notification_config,
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

        # Done; return the response.
        return response

    async def create_notification_config(self,
            request: Optional[Union[storage.CreateNotificationConfigRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            notification_config: Optional[storage.NotificationConfig] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> storage.NotificationConfig:
        r"""Creates a NotificationConfig for a given bucket.
        These NotificationConfigs, when triggered, publish
        messages to the specified Pub/Sub topics. See
        https://cloud.google.com/storage/docs/pubsub-notifications.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_create_notification_config():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                notification_config = storage_v2.NotificationConfig()
                notification_config.name = "name_value"
                notification_config.topic = "topic_value"
                notification_config.payload_format = "payload_format_value"

                request = storage_v2.CreateNotificationConfigRequest(
                    parent="parent_value",
                    notification_config=notification_config,
                )

                # Make the request
                response = await client.create_notification_config(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CreateNotificationConfigRequest, dict]]):
                The request object. Request message for
                CreateNotificationConfig.
            parent (:class:`str`):
                Required. The bucket to which this
                NotificationConfig belongs.

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            notification_config (:class:`googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.NotificationConfig`):
                Required. Properties of the
                NotificationConfig to be inserted.

                This corresponds to the ``notification_config`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.NotificationConfig:
                A directive to publish Pub/Sub
                notifications upon changes to a bucket.

        """
        warnings.warn("StorageAsyncClient.create_notification_config is deprecated",
            DeprecationWarning)

        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent, notification_config])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.CreateNotificationConfigRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent
        if notification_config is not None:
            request.notification_config = notification_config

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.create_notification_config,
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

        # Done; return the response.
        return response

    async def list_notification_configs(self,
            request: Optional[Union[storage.ListNotificationConfigsRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, str]] = (),
            ) -> pagers.ListNotificationConfigsAsyncPager:
        r"""Retrieves a list of NotificationConfigs for a given
        bucket.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import storage_v2

            async def sample_list_notification_configs():
                # Create a client
                client = storage_v2.StorageAsyncClient()

                # Initialize request argument(s)
                request = storage_v2.ListNotificationConfigsRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_notification_configs(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ListNotificationConfigsRequest, dict]]):
                The request object. Request message for
                ListNotifications.
            parent (:class:`str`):
                Required. Name of a Google Cloud
                Storage bucket.

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry.Retry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, str]]): Strings which should be
                sent along with the request as metadata.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.storage_v2.services.storage.pagers.ListNotificationConfigsAsyncPager:
                The result of a call to
                ListNotificationConfigs
                Iterating over this object will yield
                results and resolve additional pages
                automatically.

        """
        warnings.warn("StorageAsyncClient.list_notification_configs is deprecated",
            DeprecationWarning)

        # Create or coerce a protobuf request object.
        # Quick check: If we got a request object, we should *not* have
        # gotten any keyword arguments that map to the request.
        has_flattened_params = any([parent])
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        request = storage.ListNotificationConfigsRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = gapic_v1.method_async.wrap_method(
            self._client._transport.list_notification_configs,
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

        # This method is paged; wrap the response in a pager, which provides
        # an `__aiter__` convenience method.
        response = pagers.ListNotificationConfigsAsyncPager(
            method=rpc,
            request=request,
            response=response,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def __aenter__(self) -> "StorageAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.transport.close()

DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(gapic_version=package_version.__version__)


__all__ = (
    "StorageAsyncClient",
)
