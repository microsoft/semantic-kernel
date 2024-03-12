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
import google.auth  # type: ignore
from google.auth import credentials as ga_credentials  # type: ignore
from google.auth.transport.grpc import SslCredentials  # type: ignore

import grpc  # type: ignore

from google.iam.v1 import iam_policy_pb2  # type: ignore
from google.iam.v1 import policy_pb2  # type: ignore
from cloudsdk.google.protobuf import empty_pb2  # type: ignore
from google.pubsub_v1.types import pubsub
from .base import PublisherTransport, DEFAULT_CLIENT_INFO


class PublisherGrpcTransport(PublisherTransport):
    """gRPC backend transport for Publisher.

    The service that an application uses to manipulate topics,
    and to send messages to a topic.

    This class defines the same methods as the primary client, so the
    primary client can load the underlying transport implementation
    and call it.

    It sends protocol buffers over the wire using gRPC (which is built on
    top of HTTP/2); the ``grpcio`` package must be installed.
    """

    _stubs: Dict[str, Callable]

    def __init__(
        self,
        *,
        host: str = "pubsub.googleapis.com",
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
                    ("grpc.max_metadata_size", 4 * 1024 * 1024),
                    ("grpc.keepalive_time_ms", 30000),
                ],
            )

        # Wrap messages. This must be done after self._grpc_channel exists
        self._prep_wrapped_messages(client_info)

    @classmethod
    def create_channel(
        cls,
        host: str = "pubsub.googleapis.com",
        credentials: Optional[ga_credentials.Credentials] = None,
        credentials_file: Optional[str] = None,
        scopes: Optional[Sequence[str]] = None,
        quota_project_id: Optional[str] = None,
        **kwargs,
    ) -> grpc.Channel:
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
            **kwargs,
        )

    @property
    def grpc_channel(self) -> grpc.Channel:
        """Return the channel designed to connect to this service."""
        return self._grpc_channel

    @property
    def create_topic(self) -> Callable[[pubsub.Topic], pubsub.Topic]:
        r"""Return a callable for the create topic method over gRPC.

        Creates the given topic with the given name. See the [resource
        name rules]
        (https://cloud.google.com/pubsub/docs/admin#resource_names).

        Returns:
            Callable[[~.Topic],
                    ~.Topic]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "create_topic" not in self._stubs:
            self._stubs["create_topic"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Publisher/CreateTopic",
                request_serializer=pubsub.Topic.serialize,
                response_deserializer=pubsub.Topic.deserialize,
            )
        return self._stubs["create_topic"]

    @property
    def update_topic(self) -> Callable[[pubsub.UpdateTopicRequest], pubsub.Topic]:
        r"""Return a callable for the update topic method over gRPC.

        Updates an existing topic. Note that certain
        properties of a topic are not modifiable.

        Returns:
            Callable[[~.UpdateTopicRequest],
                    ~.Topic]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "update_topic" not in self._stubs:
            self._stubs["update_topic"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Publisher/UpdateTopic",
                request_serializer=pubsub.UpdateTopicRequest.serialize,
                response_deserializer=pubsub.Topic.deserialize,
            )
        return self._stubs["update_topic"]

    @property
    def publish(self) -> Callable[[pubsub.PublishRequest], pubsub.PublishResponse]:
        r"""Return a callable for the publish method over gRPC.

        Adds one or more messages to the topic. Returns ``NOT_FOUND`` if
        the topic does not exist.

        Returns:
            Callable[[~.PublishRequest],
                    ~.PublishResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "publish" not in self._stubs:
            self._stubs["publish"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Publisher/Publish",
                request_serializer=pubsub.PublishRequest.serialize,
                response_deserializer=pubsub.PublishResponse.deserialize,
            )
        return self._stubs["publish"]

    @property
    def get_topic(self) -> Callable[[pubsub.GetTopicRequest], pubsub.Topic]:
        r"""Return a callable for the get topic method over gRPC.

        Gets the configuration of a topic.

        Returns:
            Callable[[~.GetTopicRequest],
                    ~.Topic]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "get_topic" not in self._stubs:
            self._stubs["get_topic"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Publisher/GetTopic",
                request_serializer=pubsub.GetTopicRequest.serialize,
                response_deserializer=pubsub.Topic.deserialize,
            )
        return self._stubs["get_topic"]

    @property
    def list_topics(
        self,
    ) -> Callable[[pubsub.ListTopicsRequest], pubsub.ListTopicsResponse]:
        r"""Return a callable for the list topics method over gRPC.

        Lists matching topics.

        Returns:
            Callable[[~.ListTopicsRequest],
                    ~.ListTopicsResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "list_topics" not in self._stubs:
            self._stubs["list_topics"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Publisher/ListTopics",
                request_serializer=pubsub.ListTopicsRequest.serialize,
                response_deserializer=pubsub.ListTopicsResponse.deserialize,
            )
        return self._stubs["list_topics"]

    @property
    def list_topic_subscriptions(
        self,
    ) -> Callable[
        [pubsub.ListTopicSubscriptionsRequest], pubsub.ListTopicSubscriptionsResponse
    ]:
        r"""Return a callable for the list topic subscriptions method over gRPC.

        Lists the names of the attached subscriptions on this
        topic.

        Returns:
            Callable[[~.ListTopicSubscriptionsRequest],
                    ~.ListTopicSubscriptionsResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "list_topic_subscriptions" not in self._stubs:
            self._stubs["list_topic_subscriptions"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Publisher/ListTopicSubscriptions",
                request_serializer=pubsub.ListTopicSubscriptionsRequest.serialize,
                response_deserializer=pubsub.ListTopicSubscriptionsResponse.deserialize,
            )
        return self._stubs["list_topic_subscriptions"]

    @property
    def list_topic_snapshots(
        self,
    ) -> Callable[
        [pubsub.ListTopicSnapshotsRequest], pubsub.ListTopicSnapshotsResponse
    ]:
        r"""Return a callable for the list topic snapshots method over gRPC.

        Lists the names of the snapshots on this topic. Snapshots are
        used in
        `Seek <https://cloud.google.com/pubsub/docs/replay-overview>`__
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.

        Returns:
            Callable[[~.ListTopicSnapshotsRequest],
                    ~.ListTopicSnapshotsResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "list_topic_snapshots" not in self._stubs:
            self._stubs["list_topic_snapshots"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Publisher/ListTopicSnapshots",
                request_serializer=pubsub.ListTopicSnapshotsRequest.serialize,
                response_deserializer=pubsub.ListTopicSnapshotsResponse.deserialize,
            )
        return self._stubs["list_topic_snapshots"]

    @property
    def delete_topic(self) -> Callable[[pubsub.DeleteTopicRequest], empty_pb2.Empty]:
        r"""Return a callable for the delete topic method over gRPC.

        Deletes the topic with the given name. Returns ``NOT_FOUND`` if
        the topic does not exist. After a topic is deleted, a new topic
        may be created with the same name; this is an entirely new topic
        with none of the old configuration or subscriptions. Existing
        subscriptions to this topic are not deleted, but their ``topic``
        field is set to ``_deleted-topic_``.

        Returns:
            Callable[[~.DeleteTopicRequest],
                    ~.Empty]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "delete_topic" not in self._stubs:
            self._stubs["delete_topic"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Publisher/DeleteTopic",
                request_serializer=pubsub.DeleteTopicRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs["delete_topic"]

    @property
    def detach_subscription(
        self,
    ) -> Callable[
        [pubsub.DetachSubscriptionRequest], pubsub.DetachSubscriptionResponse
    ]:
        r"""Return a callable for the detach subscription method over gRPC.

        Detaches a subscription from this topic. All messages retained
        in the subscription are dropped. Subsequent ``Pull`` and
        ``StreamingPull`` requests will return FAILED_PRECONDITION. If
        the subscription is a push subscription, pushes to the endpoint
        will stop.

        Returns:
            Callable[[~.DetachSubscriptionRequest],
                    ~.DetachSubscriptionResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "detach_subscription" not in self._stubs:
            self._stubs["detach_subscription"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Publisher/DetachSubscription",
                request_serializer=pubsub.DetachSubscriptionRequest.serialize,
                response_deserializer=pubsub.DetachSubscriptionResponse.deserialize,
            )
        return self._stubs["detach_subscription"]

    @property
    def set_iam_policy(
        self,
    ) -> Callable[[iam_policy_pb2.SetIamPolicyRequest], policy_pb2.Policy]:
        r"""Return a callable for the set iam policy method over gRPC.
        Sets the IAM access control policy on the specified
        function. Replaces any existing policy.
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
    ) -> Callable[[iam_policy_pb2.GetIamPolicyRequest], policy_pb2.Policy]:
        r"""Return a callable for the get iam policy method over gRPC.
        Gets the IAM access control policy for a function.
        Returns an empty policy if the function exists and does
        not have a policy set.
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
        iam_policy_pb2.TestIamPermissionsResponse,
    ]:
        r"""Return a callable for the test iam permissions method over gRPC.
        Tests the specified permissions against the IAM access control
        policy for a function. If the function does not exist, this will
        return an empty set of permissions, not a NOT_FOUND error.
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
        if "test_iam_permissions" not in self._stubs:
            self._stubs["test_iam_permissions"] = self.grpc_channel.unary_unary(
                "/google.iam.v1.IAMPolicy/TestIamPermissions",
                request_serializer=iam_policy_pb2.TestIamPermissionsRequest.SerializeToString,
                response_deserializer=iam_policy_pb2.TestIamPermissionsResponse.FromString,
            )
        return self._stubs["test_iam_permissions"]

    def close(self):
        self.grpc_channel.close()

    @property
    def kind(self) -> str:
        return "grpc"


__all__ = ("PublisherGrpcTransport",)
