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
import warnings
from typing import Callable, Dict, Optional, Sequence, Tuple, Union

from google.api_core import grpc_helpers
from google.api_core import gapic_v1
import google.auth                         # type: ignore
from google.auth import credentials as ga_credentials  # type: ignore
from google.auth.transport.grpc import SslCredentials  # type: ignore

import grpc  # type: ignore

from google.iam.v1 import iam_policy_pb2  # type: ignore
from google.iam.v1 import policy_pb2  # type: ignore
from cloudsdk.google.protobuf import empty_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.storage_v2.types import storage
from .base import StorageTransport, DEFAULT_CLIENT_INFO


class StorageGrpcTransport(StorageTransport):
    """gRPC backend transport for Storage.

    API Overview and Naming Syntax
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

    This class defines the same methods as the primary client, so the
    primary client can load the underlying transport implementation
    and call it.

    It sends protocol buffers over the wire using gRPC (which is built on
    top of HTTP/2); the ``grpcio`` package must be installed.
    """
    _stubs: Dict[str, Callable]

    def __init__(self, *,
            host: str = 'storage.googleapis.com',
            credentials: Optional[ga_credentials.Credentials] = None,
            credentials_file: Optional[str] = None,
            scopes: Optional[Sequence[str]] = None,
            channel: Optional[grpc.Channel] = None,
            api_mtls_endpoint: Optional[str] = None,
            client_cert_source: Optional[Callable[[], Tuple[bytes, bytes]]] = None,
            ssl_channel_credentials: Optional[grpc.ChannelCredentials] = None,
            client_cert_source_for_mtls: Optional[Callable[[], Tuple[bytes, bytes]]] = None,
            quota_project_id: Optional[str] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            always_use_jwt_access: Optional[bool] = False,
            api_audience: Optional[str] = None,
            ) -> None:
        """Instantiate the transport.

        Args:
            host (Optional[str]):
                 The hostname to connect to.
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
                This argument is ignored if ``channel`` is provided.
            credentials_file (Optional[str]): A file with credentials that can
                be loaded with :func:`google.auth.load_credentials_from_file`.
                This argument is ignored if ``channel`` is provided.
            scopes (Optional(Sequence[str])): A list of scopes. This argument is
                ignored if ``channel`` is provided.
            channel (Optional[grpc.Channel]): A ``Channel`` instance through
                which to make calls.
            api_mtls_endpoint (Optional[str]): Deprecated. The mutual TLS endpoint.
                If provided, it overrides the ``host`` argument and tries to create
                a mutual TLS channel with client SSL credentials from
                ``client_cert_source`` or application default SSL credentials.
            client_cert_source (Optional[Callable[[], Tuple[bytes, bytes]]]):
                Deprecated. A callback to provide client SSL certificate bytes and
                private key bytes, both in PEM format. It is ignored if
                ``api_mtls_endpoint`` is None.
            ssl_channel_credentials (grpc.ChannelCredentials): SSL credentials
                for the grpc channel. It is ignored if ``channel`` is provided.
            client_cert_source_for_mtls (Optional[Callable[[], Tuple[bytes, bytes]]]):
                A callback to provide client certificate bytes and private key bytes,
                both in PEM format. It is used to configure a mutual TLS channel. It is
                ignored if ``channel`` or ``ssl_channel_credentials`` is provided.
            quota_project_id (Optional[str]): An optional project to use for billing
                and quota.
            client_info (google.api_core.gapic_v1.client_info.ClientInfo):
                The client info used to send a user-agent string along with
                API requests. If ``None``, then default info will be used.
                Generally, you only need to set this if you're developing
                your own client library.
            always_use_jwt_access (Optional[bool]): Whether self signed JWT should
                be used for service account credentials.

        Raises:
          google.auth.exceptions.MutualTLSChannelError: If mutual TLS transport
              creation failed for any reason.
          google.api_core.exceptions.DuplicateCredentialArgs: If both ``credentials``
              and ``credentials_file`` are passed.
        """
        self._grpc_channel = None
        self._ssl_channel_credentials = ssl_channel_credentials
        self._stubs: Dict[str, Callable] = {}

        if api_mtls_endpoint:
            warnings.warn("api_mtls_endpoint is deprecated", DeprecationWarning)
        if client_cert_source:
            warnings.warn("client_cert_source is deprecated", DeprecationWarning)

        if channel:
            # Ignore credentials if a channel was passed.
            credentials = False
            # If a channel was explicitly provided, set it.
            self._grpc_channel = channel
            self._ssl_channel_credentials = None

        else:
            if api_mtls_endpoint:
                host = api_mtls_endpoint

                # Create SSL credentials with client_cert_source or application
                # default SSL credentials.
                if client_cert_source:
                    cert, key = client_cert_source()
                    self._ssl_channel_credentials = grpc.ssl_channel_credentials(
                        certificate_chain=cert, private_key=key
                    )
                else:
                    self._ssl_channel_credentials = SslCredentials().ssl_credentials

            else:
                if client_cert_source_for_mtls and not ssl_channel_credentials:
                    cert, key = client_cert_source_for_mtls()
                    self._ssl_channel_credentials = grpc.ssl_channel_credentials(
                        certificate_chain=cert, private_key=key
                    )

        # The base transport sets the host, credentials and scopes
        super().__init__(
            host=host,
            credentials=credentials,
            credentials_file=credentials_file,
            scopes=scopes,
            quota_project_id=quota_project_id,
            client_info=client_info,
            always_use_jwt_access=always_use_jwt_access,
            api_audience=api_audience,
        )

        if not self._grpc_channel:
            self._grpc_channel = type(self).create_channel(
                self._host,
                # use the credentials which are saved
                credentials=self._credentials,
                # Set ``credentials_file`` to ``None`` here as
                # the credentials that we saved earlier should be used.
                credentials_file=None,
                scopes=self._scopes,
                ssl_credentials=self._ssl_channel_credentials,
                quota_project_id=quota_project_id,
                options=[
                    ("grpc.max_send_message_length", -1),
                    ("grpc.max_receive_message_length", -1),
                ],
            )

        # Wrap messages. This must be done after self._grpc_channel exists
        self._prep_wrapped_messages(client_info)

    @classmethod
    def create_channel(cls,
                       host: str = 'storage.googleapis.com',
                       credentials: Optional[ga_credentials.Credentials] = None,
                       credentials_file: Optional[str] = None,
                       scopes: Optional[Sequence[str]] = None,
                       quota_project_id: Optional[str] = None,
                       **kwargs) -> grpc.Channel:
        """Create and return a gRPC channel object.
        Args:
            host (Optional[str]): The host for the channel to use.
            credentials (Optional[~.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify this application to the service. If
                none are specified, the client will attempt to ascertain
                the credentials from the environment.
            credentials_file (Optional[str]): A file with credentials that can
                be loaded with :func:`google.auth.load_credentials_from_file`.
                This argument is mutually exclusive with credentials.
            scopes (Optional[Sequence[str]]): A optional list of scopes needed for this
                service. These are only used when credentials are not specified and
                are passed to :func:`google.auth.default`.
            quota_project_id (Optional[str]): An optional project to use for billing
                and quota.
            kwargs (Optional[dict]): Keyword arguments, which are passed to the
                channel creation.
        Returns:
            grpc.Channel: A gRPC channel object.

        Raises:
            google.api_core.exceptions.DuplicateCredentialArgs: If both ``credentials``
              and ``credentials_file`` are passed.
        """

        return grpc_helpers.create_channel(
            host,
            credentials=credentials,
            credentials_file=credentials_file,
            quota_project_id=quota_project_id,
            default_scopes=cls.AUTH_SCOPES,
            scopes=scopes,
            default_host=cls.DEFAULT_HOST,
            **kwargs
        )

    @property
    def grpc_channel(self) -> grpc.Channel:
        """Return the channel designed to connect to this service.
        """
        return self._grpc_channel

    @property
    def delete_bucket(self) -> Callable[
            [storage.DeleteBucketRequest],
            empty_pb2.Empty]:
        r"""Return a callable for the delete bucket method over gRPC.

        Permanently deletes an empty bucket.

        Returns:
            Callable[[~.DeleteBucketRequest],
                    ~.Empty]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'delete_bucket' not in self._stubs:
            self._stubs['delete_bucket'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/DeleteBucket',
                request_serializer=storage.DeleteBucketRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs['delete_bucket']

    @property
    def get_bucket(self) -> Callable[
            [storage.GetBucketRequest],
            storage.Bucket]:
        r"""Return a callable for the get bucket method over gRPC.

        Returns metadata for the specified bucket.

        Returns:
            Callable[[~.GetBucketRequest],
                    ~.Bucket]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'get_bucket' not in self._stubs:
            self._stubs['get_bucket'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/GetBucket',
                request_serializer=storage.GetBucketRequest.serialize,
                response_deserializer=storage.Bucket.deserialize,
            )
        return self._stubs['get_bucket']

    @property
    def create_bucket(self) -> Callable[
            [storage.CreateBucketRequest],
            storage.Bucket]:
        r"""Return a callable for the create bucket method over gRPC.

        Creates a new bucket.

        Returns:
            Callable[[~.CreateBucketRequest],
                    ~.Bucket]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'create_bucket' not in self._stubs:
            self._stubs['create_bucket'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/CreateBucket',
                request_serializer=storage.CreateBucketRequest.serialize,
                response_deserializer=storage.Bucket.deserialize,
            )
        return self._stubs['create_bucket']

    @property
    def list_buckets(self) -> Callable[
            [storage.ListBucketsRequest],
            storage.ListBucketsResponse]:
        r"""Return a callable for the list buckets method over gRPC.

        Retrieves a list of buckets for a given project.

        Returns:
            Callable[[~.ListBucketsRequest],
                    ~.ListBucketsResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'list_buckets' not in self._stubs:
            self._stubs['list_buckets'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/ListBuckets',
                request_serializer=storage.ListBucketsRequest.serialize,
                response_deserializer=storage.ListBucketsResponse.deserialize,
            )
        return self._stubs['list_buckets']

    @property
    def lock_bucket_retention_policy(self) -> Callable[
            [storage.LockBucketRetentionPolicyRequest],
            storage.Bucket]:
        r"""Return a callable for the lock bucket retention policy method over gRPC.

        Locks retention policy on a bucket.

        Returns:
            Callable[[~.LockBucketRetentionPolicyRequest],
                    ~.Bucket]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'lock_bucket_retention_policy' not in self._stubs:
            self._stubs['lock_bucket_retention_policy'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/LockBucketRetentionPolicy',
                request_serializer=storage.LockBucketRetentionPolicyRequest.serialize,
                response_deserializer=storage.Bucket.deserialize,
            )
        return self._stubs['lock_bucket_retention_policy']

    @property
    def get_iam_policy(self) -> Callable[
            [iam_policy_pb2.GetIamPolicyRequest],
            policy_pb2.Policy]:
        r"""Return a callable for the get iam policy method over gRPC.

        Gets the IAM policy for a specified bucket. The ``resource``
        field in the request should be ``projects/_/buckets/{bucket}``.

        Returns:
            Callable[[~.GetIamPolicyRequest],
                    ~.Policy]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'get_iam_policy' not in self._stubs:
            self._stubs['get_iam_policy'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/GetIamPolicy',
                request_serializer=iam_policy_pb2.GetIamPolicyRequest.SerializeToString,
                response_deserializer=policy_pb2.Policy.FromString,
            )
        return self._stubs['get_iam_policy']

    @property
    def set_iam_policy(self) -> Callable[
            [iam_policy_pb2.SetIamPolicyRequest],
            policy_pb2.Policy]:
        r"""Return a callable for the set iam policy method over gRPC.

        Updates an IAM policy for the specified bucket. The ``resource``
        field in the request should be ``projects/_/buckets/{bucket}``.

        Returns:
            Callable[[~.SetIamPolicyRequest],
                    ~.Policy]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'set_iam_policy' not in self._stubs:
            self._stubs['set_iam_policy'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/SetIamPolicy',
                request_serializer=iam_policy_pb2.SetIamPolicyRequest.SerializeToString,
                response_deserializer=policy_pb2.Policy.FromString,
            )
        return self._stubs['set_iam_policy']

    @property
    def test_iam_permissions(self) -> Callable[
            [iam_policy_pb2.TestIamPermissionsRequest],
            iam_policy_pb2.TestIamPermissionsResponse]:
        r"""Return a callable for the test iam permissions method over gRPC.

        Tests a set of permissions on the given bucket or object to see
        which, if any, are held by the caller. The ``resource`` field in
        the request should be ``projects/_/buckets/{bucket}`` for a
        bucket or ``projects/_/buckets/{bucket}/objects/{object}`` for
        an object.

        Returns:
            Callable[[~.TestIamPermissionsRequest],
                    ~.TestIamPermissionsResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'test_iam_permissions' not in self._stubs:
            self._stubs['test_iam_permissions'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/TestIamPermissions',
                request_serializer=iam_policy_pb2.TestIamPermissionsRequest.SerializeToString,
                response_deserializer=iam_policy_pb2.TestIamPermissionsResponse.FromString,
            )
        return self._stubs['test_iam_permissions']

    @property
    def update_bucket(self) -> Callable[
            [storage.UpdateBucketRequest],
            storage.Bucket]:
        r"""Return a callable for the update bucket method over gRPC.

        Updates a bucket. Equivalent to JSON API's
        storage.buckets.patch method.

        Returns:
            Callable[[~.UpdateBucketRequest],
                    ~.Bucket]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'update_bucket' not in self._stubs:
            self._stubs['update_bucket'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/UpdateBucket',
                request_serializer=storage.UpdateBucketRequest.serialize,
                response_deserializer=storage.Bucket.deserialize,
            )
        return self._stubs['update_bucket']

    @property
    def compose_object(self) -> Callable[
            [storage.ComposeObjectRequest],
            storage.Object]:
        r"""Return a callable for the compose object method over gRPC.

        Concatenates a list of existing objects into a new
        object in the same bucket.

        Returns:
            Callable[[~.ComposeObjectRequest],
                    ~.Object]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'compose_object' not in self._stubs:
            self._stubs['compose_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/ComposeObject',
                request_serializer=storage.ComposeObjectRequest.serialize,
                response_deserializer=storage.Object.deserialize,
            )
        return self._stubs['compose_object']

    @property
    def delete_object(self) -> Callable[
            [storage.DeleteObjectRequest],
            empty_pb2.Empty]:
        r"""Return a callable for the delete object method over gRPC.

        Deletes an object and its metadata.

        Deletions are normally permanent when versioning is
        disabled or whenever the generation parameter is used.
        However, if soft delete is enabled for the bucket,
        deleted objects can be restored using RestoreObject
        until the soft delete retention period has passed.

        Returns:
            Callable[[~.DeleteObjectRequest],
                    ~.Empty]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'delete_object' not in self._stubs:
            self._stubs['delete_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/DeleteObject',
                request_serializer=storage.DeleteObjectRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs['delete_object']

    @property
    def restore_object(self) -> Callable[
            [storage.RestoreObjectRequest],
            storage.Object]:
        r"""Return a callable for the restore object method over gRPC.

        Restores a soft-deleted object.

        Returns:
            Callable[[~.RestoreObjectRequest],
                    ~.Object]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'restore_object' not in self._stubs:
            self._stubs['restore_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/RestoreObject',
                request_serializer=storage.RestoreObjectRequest.serialize,
                response_deserializer=storage.Object.deserialize,
            )
        return self._stubs['restore_object']

    @property
    def cancel_resumable_write(self) -> Callable[
            [storage.CancelResumableWriteRequest],
            storage.CancelResumableWriteResponse]:
        r"""Return a callable for the cancel resumable write method over gRPC.

        Cancels an in-progress resumable upload.

        Any attempts to write to the resumable upload after
        cancelling the upload will fail.

        The behavior for currently in progress write operations
        is not guaranteed - they could either complete before
        the cancellation or fail if the cancellation completes
        first.

        Returns:
            Callable[[~.CancelResumableWriteRequest],
                    ~.CancelResumableWriteResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'cancel_resumable_write' not in self._stubs:
            self._stubs['cancel_resumable_write'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/CancelResumableWrite',
                request_serializer=storage.CancelResumableWriteRequest.serialize,
                response_deserializer=storage.CancelResumableWriteResponse.deserialize,
            )
        return self._stubs['cancel_resumable_write']

    @property
    def get_object(self) -> Callable[
            [storage.GetObjectRequest],
            storage.Object]:
        r"""Return a callable for the get object method over gRPC.

        Retrieves an object's metadata.

        Returns:
            Callable[[~.GetObjectRequest],
                    ~.Object]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'get_object' not in self._stubs:
            self._stubs['get_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/GetObject',
                request_serializer=storage.GetObjectRequest.serialize,
                response_deserializer=storage.Object.deserialize,
            )
        return self._stubs['get_object']

    @property
    def read_object(self) -> Callable[
            [storage.ReadObjectRequest],
            storage.ReadObjectResponse]:
        r"""Return a callable for the read object method over gRPC.

        Reads an object's data.

        Returns:
            Callable[[~.ReadObjectRequest],
                    ~.ReadObjectResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'read_object' not in self._stubs:
            self._stubs['read_object'] = self.grpc_channel.unary_stream(
                '/google.storage.v2.Storage/ReadObject',
                request_serializer=storage.ReadObjectRequest.serialize,
                response_deserializer=storage.ReadObjectResponse.deserialize,
            )
        return self._stubs['read_object']

    @property
    def update_object(self) -> Callable[
            [storage.UpdateObjectRequest],
            storage.Object]:
        r"""Return a callable for the update object method over gRPC.

        Updates an object's metadata.
        Equivalent to JSON API's storage.objects.patch.

        Returns:
            Callable[[~.UpdateObjectRequest],
                    ~.Object]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'update_object' not in self._stubs:
            self._stubs['update_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/UpdateObject',
                request_serializer=storage.UpdateObjectRequest.serialize,
                response_deserializer=storage.Object.deserialize,
            )
        return self._stubs['update_object']

    @property
    def write_object(self) -> Callable[
            [storage.WriteObjectRequest],
            storage.WriteObjectResponse]:
        r"""Return a callable for the write object method over gRPC.

        Stores a new object and metadata.

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

        Returns:
            Callable[[~.WriteObjectRequest],
                    ~.WriteObjectResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'write_object' not in self._stubs:
            self._stubs['write_object'] = self.grpc_channel.stream_unary(
                '/google.storage.v2.Storage/WriteObject',
                request_serializer=storage.WriteObjectRequest.serialize,
                response_deserializer=storage.WriteObjectResponse.deserialize,
            )
        return self._stubs['write_object']

    @property
    def bidi_write_object(self) -> Callable[
            [storage.BidiWriteObjectRequest],
            storage.BidiWriteObjectResponse]:
        r"""Return a callable for the bidi write object method over gRPC.

        Stores a new object and metadata.

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

        Returns:
            Callable[[~.BidiWriteObjectRequest],
                    ~.BidiWriteObjectResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'bidi_write_object' not in self._stubs:
            self._stubs['bidi_write_object'] = self.grpc_channel.stream_stream(
                '/google.storage.v2.Storage/BidiWriteObject',
                request_serializer=storage.BidiWriteObjectRequest.serialize,
                response_deserializer=storage.BidiWriteObjectResponse.deserialize,
            )
        return self._stubs['bidi_write_object']

    @property
    def list_objects(self) -> Callable[
            [storage.ListObjectsRequest],
            storage.ListObjectsResponse]:
        r"""Return a callable for the list objects method over gRPC.

        Retrieves a list of objects matching the criteria.

        Returns:
            Callable[[~.ListObjectsRequest],
                    ~.ListObjectsResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'list_objects' not in self._stubs:
            self._stubs['list_objects'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/ListObjects',
                request_serializer=storage.ListObjectsRequest.serialize,
                response_deserializer=storage.ListObjectsResponse.deserialize,
            )
        return self._stubs['list_objects']

    @property
    def rewrite_object(self) -> Callable[
            [storage.RewriteObjectRequest],
            storage.RewriteResponse]:
        r"""Return a callable for the rewrite object method over gRPC.

        Rewrites a source object to a destination object.
        Optionally overrides metadata.

        Returns:
            Callable[[~.RewriteObjectRequest],
                    ~.RewriteResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'rewrite_object' not in self._stubs:
            self._stubs['rewrite_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/RewriteObject',
                request_serializer=storage.RewriteObjectRequest.serialize,
                response_deserializer=storage.RewriteResponse.deserialize,
            )
        return self._stubs['rewrite_object']

    @property
    def start_resumable_write(self) -> Callable[
            [storage.StartResumableWriteRequest],
            storage.StartResumableWriteResponse]:
        r"""Return a callable for the start resumable write method over gRPC.

        Starts a resumable write. How long the write
        operation remains valid, and what happens when the write
        operation becomes invalid, are service-dependent.

        Returns:
            Callable[[~.StartResumableWriteRequest],
                    ~.StartResumableWriteResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'start_resumable_write' not in self._stubs:
            self._stubs['start_resumable_write'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/StartResumableWrite',
                request_serializer=storage.StartResumableWriteRequest.serialize,
                response_deserializer=storage.StartResumableWriteResponse.deserialize,
            )
        return self._stubs['start_resumable_write']

    @property
    def query_write_status(self) -> Callable[
            [storage.QueryWriteStatusRequest],
            storage.QueryWriteStatusResponse]:
        r"""Return a callable for the query write status method over gRPC.

        Determines the ``persisted_size`` for an object that is being
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

        Returns:
            Callable[[~.QueryWriteStatusRequest],
                    ~.QueryWriteStatusResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'query_write_status' not in self._stubs:
            self._stubs['query_write_status'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/QueryWriteStatus',
                request_serializer=storage.QueryWriteStatusRequest.serialize,
                response_deserializer=storage.QueryWriteStatusResponse.deserialize,
            )
        return self._stubs['query_write_status']

    @property
    def get_service_account(self) -> Callable[
            [storage.GetServiceAccountRequest],
            storage.ServiceAccount]:
        r"""Return a callable for the get service account method over gRPC.

        Retrieves the name of a project's Google Cloud
        Storage service account.

        Returns:
            Callable[[~.GetServiceAccountRequest],
                    ~.ServiceAccount]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'get_service_account' not in self._stubs:
            self._stubs['get_service_account'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/GetServiceAccount',
                request_serializer=storage.GetServiceAccountRequest.serialize,
                response_deserializer=storage.ServiceAccount.deserialize,
            )
        return self._stubs['get_service_account']

    @property
    def create_hmac_key(self) -> Callable[
            [storage.CreateHmacKeyRequest],
            storage.CreateHmacKeyResponse]:
        r"""Return a callable for the create hmac key method over gRPC.

        Creates a new HMAC key for the given service account.

        Returns:
            Callable[[~.CreateHmacKeyRequest],
                    ~.CreateHmacKeyResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'create_hmac_key' not in self._stubs:
            self._stubs['create_hmac_key'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/CreateHmacKey',
                request_serializer=storage.CreateHmacKeyRequest.serialize,
                response_deserializer=storage.CreateHmacKeyResponse.deserialize,
            )
        return self._stubs['create_hmac_key']

    @property
    def delete_hmac_key(self) -> Callable[
            [storage.DeleteHmacKeyRequest],
            empty_pb2.Empty]:
        r"""Return a callable for the delete hmac key method over gRPC.

        Deletes a given HMAC key.  Key must be in an INACTIVE
        state.

        Returns:
            Callable[[~.DeleteHmacKeyRequest],
                    ~.Empty]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'delete_hmac_key' not in self._stubs:
            self._stubs['delete_hmac_key'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/DeleteHmacKey',
                request_serializer=storage.DeleteHmacKeyRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs['delete_hmac_key']

    @property
    def get_hmac_key(self) -> Callable[
            [storage.GetHmacKeyRequest],
            storage.HmacKeyMetadata]:
        r"""Return a callable for the get hmac key method over gRPC.

        Gets an existing HMAC key metadata for the given id.

        Returns:
            Callable[[~.GetHmacKeyRequest],
                    ~.HmacKeyMetadata]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'get_hmac_key' not in self._stubs:
            self._stubs['get_hmac_key'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/GetHmacKey',
                request_serializer=storage.GetHmacKeyRequest.serialize,
                response_deserializer=storage.HmacKeyMetadata.deserialize,
            )
        return self._stubs['get_hmac_key']

    @property
    def list_hmac_keys(self) -> Callable[
            [storage.ListHmacKeysRequest],
            storage.ListHmacKeysResponse]:
        r"""Return a callable for the list hmac keys method over gRPC.

        Lists HMAC keys under a given project with the
        additional filters provided.

        Returns:
            Callable[[~.ListHmacKeysRequest],
                    ~.ListHmacKeysResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'list_hmac_keys' not in self._stubs:
            self._stubs['list_hmac_keys'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/ListHmacKeys',
                request_serializer=storage.ListHmacKeysRequest.serialize,
                response_deserializer=storage.ListHmacKeysResponse.deserialize,
            )
        return self._stubs['list_hmac_keys']

    @property
    def update_hmac_key(self) -> Callable[
            [storage.UpdateHmacKeyRequest],
            storage.HmacKeyMetadata]:
        r"""Return a callable for the update hmac key method over gRPC.

        Updates a given HMAC key state between ACTIVE and
        INACTIVE.

        Returns:
            Callable[[~.UpdateHmacKeyRequest],
                    ~.HmacKeyMetadata]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'update_hmac_key' not in self._stubs:
            self._stubs['update_hmac_key'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/UpdateHmacKey',
                request_serializer=storage.UpdateHmacKeyRequest.serialize,
                response_deserializer=storage.HmacKeyMetadata.deserialize,
            )
        return self._stubs['update_hmac_key']

    @property
    def delete_notification_config(self) -> Callable[
            [storage.DeleteNotificationConfigRequest],
            empty_pb2.Empty]:
        r"""Return a callable for the delete notification config method over gRPC.

        Permanently deletes a NotificationConfig.

        Returns:
            Callable[[~.DeleteNotificationConfigRequest],
                    ~.Empty]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'delete_notification_config' not in self._stubs:
            self._stubs['delete_notification_config'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/DeleteNotificationConfig',
                request_serializer=storage.DeleteNotificationConfigRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs['delete_notification_config']

    @property
    def get_notification_config(self) -> Callable[
            [storage.GetNotificationConfigRequest],
            storage.NotificationConfig]:
        r"""Return a callable for the get notification config method over gRPC.

        View a NotificationConfig.

        Returns:
            Callable[[~.GetNotificationConfigRequest],
                    ~.NotificationConfig]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'get_notification_config' not in self._stubs:
            self._stubs['get_notification_config'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/GetNotificationConfig',
                request_serializer=storage.GetNotificationConfigRequest.serialize,
                response_deserializer=storage.NotificationConfig.deserialize,
            )
        return self._stubs['get_notification_config']

    @property
    def create_notification_config(self) -> Callable[
            [storage.CreateNotificationConfigRequest],
            storage.NotificationConfig]:
        r"""Return a callable for the create notification config method over gRPC.

        Creates a NotificationConfig for a given bucket.
        These NotificationConfigs, when triggered, publish
        messages to the specified Pub/Sub topics. See
        https://cloud.google.com/storage/docs/pubsub-notifications.

        Returns:
            Callable[[~.CreateNotificationConfigRequest],
                    ~.NotificationConfig]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'create_notification_config' not in self._stubs:
            self._stubs['create_notification_config'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/CreateNotificationConfig',
                request_serializer=storage.CreateNotificationConfigRequest.serialize,
                response_deserializer=storage.NotificationConfig.deserialize,
            )
        return self._stubs['create_notification_config']

    @property
    def list_notification_configs(self) -> Callable[
            [storage.ListNotificationConfigsRequest],
            storage.ListNotificationConfigsResponse]:
        r"""Return a callable for the list notification configs method over gRPC.

        Retrieves a list of NotificationConfigs for a given
        bucket.

        Returns:
            Callable[[~.ListNotificationConfigsRequest],
                    ~.ListNotificationConfigsResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'list_notification_configs' not in self._stubs:
            self._stubs['list_notification_configs'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/ListNotificationConfigs',
                request_serializer=storage.ListNotificationConfigsRequest.serialize,
                response_deserializer=storage.ListNotificationConfigsResponse.deserialize,
            )
        return self._stubs['list_notification_configs']

    def close(self):
        self.grpc_channel.close()

    @property
    def kind(self) -> str:
        return "grpc"


__all__ = (
    'StorageGrpcTransport',
)
