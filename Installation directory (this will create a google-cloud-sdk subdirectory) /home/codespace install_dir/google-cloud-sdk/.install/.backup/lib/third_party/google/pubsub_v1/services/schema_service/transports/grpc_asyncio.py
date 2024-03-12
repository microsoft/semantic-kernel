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
from typing import Awaitable, Callable, Dict, Optional, Sequence, Tuple, Union

from google.api_core import gapic_v1
from google.api_core import grpc_helpers_async
from google.auth import credentials as ga_credentials  # type: ignore
from google.auth.transport.grpc import SslCredentials  # type: ignore

import grpc  # type: ignore
from grpc.experimental import aio  # type: ignore

from google.iam.v1 import iam_policy_pb2  # type: ignore
from google.iam.v1 import policy_pb2  # type: ignore
from cloudsdk.google.protobuf import empty_pb2  # type: ignore
from google.pubsub_v1.types import schema
from google.pubsub_v1.types import schema as gp_schema
from .base import SchemaServiceTransport, DEFAULT_CLIENT_INFO
from .grpc import SchemaServiceGrpcTransport


class SchemaServiceGrpcAsyncIOTransport(SchemaServiceTransport):
    """gRPC AsyncIO backend transport for SchemaService.

    Service for doing schema-related operations.

    This class defines the same methods as the primary client, so the
    primary client can load the underlying transport implementation
    and call it.

    It sends protocol buffers over the wire using gRPC (which is built on
    top of HTTP/2); the ``grpcio`` package must be installed.
    """

    _grpc_channel: aio.Channel
    _stubs: Dict[str, Callable] = {}

    @classmethod
    def create_channel(
        cls,
        host: str = "pubsub.googleapis.com",
        credentials: Optional[ga_credentials.Credentials] = None,
        credentials_file: Optional[str] = None,
        scopes: Optional[Sequence[str]] = None,
        quota_project_id: Optional[str] = None,
        **kwargs,
    ) -> aio.Channel:
        """Create and return a gRPC AsyncIO channel object.
        Args:
            host (Optional[str]): The host for the channel to use.
            credentials (Optional[~.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify this application to the service. If
                none are specified, the client will attempt to ascertain
                the credentials from the environment.
            credentials_file (Optional[str]): A file with credentials that can
                be loaded with :func:`google.auth.load_credentials_from_file`.
                This argument is ignored if ``channel`` is provided.
            scopes (Optional[Sequence[str]]): A optional list of scopes needed for this
                service. These are only used when credentials are not specified and
                are passed to :func:`google.auth.default`.
            quota_project_id (Optional[str]): An optional project to use for billing
                and quota.
            kwargs (Optional[dict]): Keyword arguments, which are passed to the
                channel creation.
        Returns:
            aio.Channel: A gRPC AsyncIO channel object.
        """

        return grpc_helpers_async.create_channel(
            host,
            credentials=credentials,
            credentials_file=credentials_file,
            quota_project_id=quota_project_id,
            default_scopes=cls.AUTH_SCOPES,
            scopes=scopes,
            default_host=cls.DEFAULT_HOST,
            **kwargs,
        )

    def __init__(
        self,
        *,
        host: str = "pubsub.googleapis.com",
        credentials: Optional[ga_credentials.Credentials] = None,
        credentials_file: Optional[str] = None,
        scopes: Optional[Sequence[str]] = None,
        channel: Optional[aio.Channel] = None,
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
            scopes (Optional[Sequence[str]]): A optional list of scopes needed for this
                service. These are only used when credentials are not specified and
                are passed to :func:`google.auth.default`.
            channel (Optional[aio.Channel]): A ``Channel`` instance through
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
            google.auth.exceptions.MutualTlsChannelError: If mutual TLS transport
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
                    ("grpc.max_metadata_size", 4 * 1024 * 1024),
                    ("grpc.keepalive_time_ms", 30000),
                ],
            )

        # Wrap messages. This must be done after self._grpc_channel exists
        self._prep_wrapped_messages(client_info)

    @property
    def grpc_channel(self) -> aio.Channel:
        """Create the channel designed to connect to this service.

        This property caches on the instance; repeated calls return
        the same channel.
        """
        # Return the channel from cache.
        return self._grpc_channel

    @property
    def create_schema(
        self,
    ) -> Callable[[gp_schema.CreateSchemaRequest], Awaitable[gp_schema.Schema]]:
        r"""Return a callable for the create schema method over gRPC.

        Creates a schema.

        Returns:
            Callable[[~.CreateSchemaRequest],
                    Awaitable[~.Schema]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "create_schema" not in self._stubs:
            self._stubs["create_schema"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.SchemaService/CreateSchema",
                request_serializer=gp_schema.CreateSchemaRequest.serialize,
                response_deserializer=gp_schema.Schema.deserialize,
            )
        return self._stubs["create_schema"]

    @property
    def get_schema(
        self,
    ) -> Callable[[schema.GetSchemaRequest], Awaitable[schema.Schema]]:
        r"""Return a callable for the get schema method over gRPC.

        Gets a schema.

        Returns:
            Callable[[~.GetSchemaRequest],
                    Awaitable[~.Schema]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "get_schema" not in self._stubs:
            self._stubs["get_schema"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.SchemaService/GetSchema",
                request_serializer=schema.GetSchemaRequest.serialize,
                response_deserializer=schema.Schema.deserialize,
            )
        return self._stubs["get_schema"]

    @property
    def list_schemas(
        self,
    ) -> Callable[[schema.ListSchemasRequest], Awaitable[schema.ListSchemasResponse]]:
        r"""Return a callable for the list schemas method over gRPC.

        Lists schemas in a project.

        Returns:
            Callable[[~.ListSchemasRequest],
                    Awaitable[~.ListSchemasResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "list_schemas" not in self._stubs:
            self._stubs["list_schemas"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.SchemaService/ListSchemas",
                request_serializer=schema.ListSchemasRequest.serialize,
                response_deserializer=schema.ListSchemasResponse.deserialize,
            )
        return self._stubs["list_schemas"]

    @property
    def list_schema_revisions(
        self,
    ) -> Callable[
        [schema.ListSchemaRevisionsRequest],
        Awaitable[schema.ListSchemaRevisionsResponse],
    ]:
        r"""Return a callable for the list schema revisions method over gRPC.

        Lists all schema revisions for the named schema.

        Returns:
            Callable[[~.ListSchemaRevisionsRequest],
                    Awaitable[~.ListSchemaRevisionsResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "list_schema_revisions" not in self._stubs:
            self._stubs["list_schema_revisions"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.SchemaService/ListSchemaRevisions",
                request_serializer=schema.ListSchemaRevisionsRequest.serialize,
                response_deserializer=schema.ListSchemaRevisionsResponse.deserialize,
            )
        return self._stubs["list_schema_revisions"]

    @property
    def commit_schema(
        self,
    ) -> Callable[[gp_schema.CommitSchemaRequest], Awaitable[gp_schema.Schema]]:
        r"""Return a callable for the commit schema method over gRPC.

        Commits a new schema revision to an existing schema.

        Returns:
            Callable[[~.CommitSchemaRequest],
                    Awaitable[~.Schema]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "commit_schema" not in self._stubs:
            self._stubs["commit_schema"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.SchemaService/CommitSchema",
                request_serializer=gp_schema.CommitSchemaRequest.serialize,
                response_deserializer=gp_schema.Schema.deserialize,
            )
        return self._stubs["commit_schema"]

    @property
    def rollback_schema(
        self,
    ) -> Callable[[schema.RollbackSchemaRequest], Awaitable[schema.Schema]]:
        r"""Return a callable for the rollback schema method over gRPC.

        Creates a new schema revision that is a copy of the provided
        revision_id.

        Returns:
            Callable[[~.RollbackSchemaRequest],
                    Awaitable[~.Schema]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "rollback_schema" not in self._stubs:
            self._stubs["rollback_schema"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.SchemaService/RollbackSchema",
                request_serializer=schema.RollbackSchemaRequest.serialize,
                response_deserializer=schema.Schema.deserialize,
            )
        return self._stubs["rollback_schema"]

    @property
    def delete_schema_revision(
        self,
    ) -> Callable[[schema.DeleteSchemaRevisionRequest], Awaitable[schema.Schema]]:
        r"""Return a callable for the delete schema revision method over gRPC.

        Deletes a specific schema revision.

        Returns:
            Callable[[~.DeleteSchemaRevisionRequest],
                    Awaitable[~.Schema]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "delete_schema_revision" not in self._stubs:
            self._stubs["delete_schema_revision"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.SchemaService/DeleteSchemaRevision",
                request_serializer=schema.DeleteSchemaRevisionRequest.serialize,
                response_deserializer=schema.Schema.deserialize,
            )
        return self._stubs["delete_schema_revision"]

    @property
    def delete_schema(
        self,
    ) -> Callable[[schema.DeleteSchemaRequest], Awaitable[empty_pb2.Empty]]:
        r"""Return a callable for the delete schema method over gRPC.

        Deletes a schema.

        Returns:
            Callable[[~.DeleteSchemaRequest],
                    Awaitable[~.Empty]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "delete_schema" not in self._stubs:
            self._stubs["delete_schema"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.SchemaService/DeleteSchema",
                request_serializer=schema.DeleteSchemaRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs["delete_schema"]

    @property
    def validate_schema(
        self,
    ) -> Callable[
        [gp_schema.ValidateSchemaRequest], Awaitable[gp_schema.ValidateSchemaResponse]
    ]:
        r"""Return a callable for the validate schema method over gRPC.

        Validates a schema.

        Returns:
            Callable[[~.ValidateSchemaRequest],
                    Awaitable[~.ValidateSchemaResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "validate_schema" not in self._stubs:
            self._stubs["validate_schema"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.SchemaService/ValidateSchema",
                request_serializer=gp_schema.ValidateSchemaRequest.serialize,
                response_deserializer=gp_schema.ValidateSchemaResponse.deserialize,
            )
        return self._stubs["validate_schema"]

    @property
    def validate_message(
        self,
    ) -> Callable[
        [schema.ValidateMessageRequest], Awaitable[schema.ValidateMessageResponse]
    ]:
        r"""Return a callable for the validate message method over gRPC.

        Validates a message against a schema.

        Returns:
            Callable[[~.ValidateMessageRequest],
                    Awaitable[~.ValidateMessageResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "validate_message" not in self._stubs:
            self._stubs["validate_message"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.SchemaService/ValidateMessage",
                request_serializer=schema.ValidateMessageRequest.serialize,
                response_deserializer=schema.ValidateMessageResponse.deserialize,
            )
        return self._stubs["validate_message"]

    @property
    def set_iam_policy(
        self,
    ) -> Callable[[iam_policy_pb2.SetIamPolicyRequest], Awaitable[policy_pb2.Policy]]:
        r"""Return a callable for the set iam policy method over gRPC.
        Sets the IAM access control policy on the specified
        function. Replaces any existing policy.
        Returns:
            Callable[[~.SetIamPolicyRequest],
                    Awaitable[~.Policy]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "set_iam_policy" not in self._stubs:
            self._stubs["set_iam_policy"] = self.grpc_channel.unary_unary(
                "/google.iam.v1.IAMPolicy/SetIamPolicy",
                request_serializer=iam_policy_pb2.SetIamPolicyRequest.SerializeToString,
                response_deserializer=policy_pb2.Policy.FromString,
            )
        return self._stubs["set_iam_policy"]

    @property
    def get_iam_policy(
        self,
    ) -> Callable[[iam_policy_pb2.GetIamPolicyRequest], Awaitable[policy_pb2.Policy]]:
        r"""Return a callable for the get iam policy method over gRPC.
        Gets the IAM access control policy for a function.
        Returns an empty policy if the function exists and does
        not have a policy set.
        Returns:
            Callable[[~.GetIamPolicyRequest],
                    Awaitable[~.Policy]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "get_iam_policy" not in self._stubs:
            self._stubs["get_iam_policy"] = self.grpc_channel.unary_unary(
                "/google.iam.v1.IAMPolicy/GetIamPolicy",
                request_serializer=iam_policy_pb2.GetIamPolicyRequest.SerializeToString,
                response_deserializer=policy_pb2.Policy.FromString,
            )
        return self._stubs["get_iam_policy"]

    @property
    def test_iam_permissions(
        self,
    ) -> Callable[
        [iam_policy_pb2.TestIamPermissionsRequest],
        Awaitable[iam_policy_pb2.TestIamPermissionsResponse],
    ]:
        r"""Return a callable for the test iam permissions method over gRPC.
        Tests the specified permissions against the IAM access control
        policy for a function. If the function does not exist, this will
        return an empty set of permissions, not a NOT_FOUND error.
        Returns:
            Callable[[~.TestIamPermissionsRequest],
                    Awaitable[~.TestIamPermissionsResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "test_iam_permissions" not in self._stubs:
            self._stubs["test_iam_permissions"] = self.grpc_channel.unary_unary(
                "/google.iam.v1.IAMPolicy/TestIamPermissions",
                request_serializer=iam_policy_pb2.TestIamPermissionsRequest.SerializeToString,
                response_deserializer=iam_policy_pb2.TestIamPermissionsResponse.FromString,
            )
        return self._stubs["test_iam_permissions"]

    def close(self):
        return self.grpc_channel.close()


__all__ = ("SchemaServiceGrpcAsyncIOTransport",)
