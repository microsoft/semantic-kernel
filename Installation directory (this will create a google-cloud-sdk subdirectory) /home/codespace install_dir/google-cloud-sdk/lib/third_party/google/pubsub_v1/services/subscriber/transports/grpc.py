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
from .base import SubscriberTransport, DEFAULT_CLIENT_INFO


class SubscriberGrpcTransport(SubscriberTransport):
    """gRPC backend transport for Subscriber.

    The service that an application uses to manipulate subscriptions and
    to consume messages from a subscription via the ``Pull`` method or
    by establishing a bi-directional stream using the ``StreamingPull``
    method.

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
    def create_subscription(
        self,
    ) -> Callable[[pubsub.Subscription], pubsub.Subscription]:
        r"""Return a callable for the create subscription method over gRPC.

        Creates a subscription to a given topic. See the [resource name
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

        Returns:
            Callable[[~.Subscription],
                    ~.Subscription]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "create_subscription" not in self._stubs:
            self._stubs["create_subscription"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/CreateSubscription",
                request_serializer=pubsub.Subscription.serialize,
                response_deserializer=pubsub.Subscription.deserialize,
            )
        return self._stubs["create_subscription"]

    @property
    def get_subscription(
        self,
    ) -> Callable[[pubsub.GetSubscriptionRequest], pubsub.Subscription]:
        r"""Return a callable for the get subscription method over gRPC.

        Gets the configuration details of a subscription.

        Returns:
            Callable[[~.GetSubscriptionRequest],
                    ~.Subscription]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "get_subscription" not in self._stubs:
            self._stubs["get_subscription"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/GetSubscription",
                request_serializer=pubsub.GetSubscriptionRequest.serialize,
                response_deserializer=pubsub.Subscription.deserialize,
            )
        return self._stubs["get_subscription"]

    @property
    def update_subscription(
        self,
    ) -> Callable[[pubsub.UpdateSubscriptionRequest], pubsub.Subscription]:
        r"""Return a callable for the update subscription method over gRPC.

        Updates an existing subscription. Note that certain
        properties of a subscription, such as its topic, are not
        modifiable.

        Returns:
            Callable[[~.UpdateSubscriptionRequest],
                    ~.Subscription]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "update_subscription" not in self._stubs:
            self._stubs["update_subscription"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/UpdateSubscription",
                request_serializer=pubsub.UpdateSubscriptionRequest.serialize,
                response_deserializer=pubsub.Subscription.deserialize,
            )
        return self._stubs["update_subscription"]

    @property
    def list_subscriptions(
        self,
    ) -> Callable[[pubsub.ListSubscriptionsRequest], pubsub.ListSubscriptionsResponse]:
        r"""Return a callable for the list subscriptions method over gRPC.

        Lists matching subscriptions.

        Returns:
            Callable[[~.ListSubscriptionsRequest],
                    ~.ListSubscriptionsResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "list_subscriptions" not in self._stubs:
            self._stubs["list_subscriptions"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/ListSubscriptions",
                request_serializer=pubsub.ListSubscriptionsRequest.serialize,
                response_deserializer=pubsub.ListSubscriptionsResponse.deserialize,
            )
        return self._stubs["list_subscriptions"]

    @property
    def delete_subscription(
        self,
    ) -> Callable[[pubsub.DeleteSubscriptionRequest], empty_pb2.Empty]:
        r"""Return a callable for the delete subscription method over gRPC.

        Deletes an existing subscription. All messages retained in the
        subscription are immediately dropped. Calls to ``Pull`` after
        deletion will return ``NOT_FOUND``. After a subscription is
        deleted, a new one may be created with the same name, but the
        new one has no association with the old subscription or its
        topic unless the same topic is specified.

        Returns:
            Callable[[~.DeleteSubscriptionRequest],
                    ~.Empty]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "delete_subscription" not in self._stubs:
            self._stubs["delete_subscription"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/DeleteSubscription",
                request_serializer=pubsub.DeleteSubscriptionRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs["delete_subscription"]

    @property
    def modify_ack_deadline(
        self,
    ) -> Callable[[pubsub.ModifyAckDeadlineRequest], empty_pb2.Empty]:
        r"""Return a callable for the modify ack deadline method over gRPC.

        Modifies the ack deadline for a specific message. This method is
        useful to indicate that more time is needed to process a message
        by the subscriber, or to make the message available for
        redelivery if the processing was interrupted. Note that this
        does not modify the subscription-level ``ackDeadlineSeconds``
        used for subsequent messages.

        Returns:
            Callable[[~.ModifyAckDeadlineRequest],
                    ~.Empty]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "modify_ack_deadline" not in self._stubs:
            self._stubs["modify_ack_deadline"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/ModifyAckDeadline",
                request_serializer=pubsub.ModifyAckDeadlineRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs["modify_ack_deadline"]

    @property
    def acknowledge(self) -> Callable[[pubsub.AcknowledgeRequest], empty_pb2.Empty]:
        r"""Return a callable for the acknowledge method over gRPC.

        Acknowledges the messages associated with the ``ack_ids`` in the
        ``AcknowledgeRequest``. The Pub/Sub system can remove the
        relevant messages from the subscription.

        Acknowledging a message whose ack deadline has expired may
        succeed, but such a message may be redelivered later.
        Acknowledging a message more than once will not result in an
        error.

        Returns:
            Callable[[~.AcknowledgeRequest],
                    ~.Empty]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "acknowledge" not in self._stubs:
            self._stubs["acknowledge"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/Acknowledge",
                request_serializer=pubsub.AcknowledgeRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs["acknowledge"]

    @property
    def pull(self) -> Callable[[pubsub.PullRequest], pubsub.PullResponse]:
        r"""Return a callable for the pull method over gRPC.

        Pulls messages from the server.

        Returns:
            Callable[[~.PullRequest],
                    ~.PullResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "pull" not in self._stubs:
            self._stubs["pull"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/Pull",
                request_serializer=pubsub.PullRequest.serialize,
                response_deserializer=pubsub.PullResponse.deserialize,
            )
        return self._stubs["pull"]

    @property
    def streaming_pull(
        self,
    ) -> Callable[[pubsub.StreamingPullRequest], pubsub.StreamingPullResponse]:
        r"""Return a callable for the streaming pull method over gRPC.

        Establishes a stream with the server, which sends messages down
        to the client. The client streams acknowledgements and ack
        deadline modifications back to the server. The server will close
        the stream and return the status on any error. The server may
        close the stream with status ``UNAVAILABLE`` to reassign
        server-side resources, in which case, the client should
        re-establish the stream. Flow control can be achieved by
        configuring the underlying RPC channel.

        Returns:
            Callable[[~.StreamingPullRequest],
                    ~.StreamingPullResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "streaming_pull" not in self._stubs:
            self._stubs["streaming_pull"] = self.grpc_channel.stream_stream(
                "/google.pubsub.v1.Subscriber/StreamingPull",
                request_serializer=pubsub.StreamingPullRequest.serialize,
                response_deserializer=pubsub.StreamingPullResponse.deserialize,
            )
        return self._stubs["streaming_pull"]

    @property
    def modify_push_config(
        self,
    ) -> Callable[[pubsub.ModifyPushConfigRequest], empty_pb2.Empty]:
        r"""Return a callable for the modify push config method over gRPC.

        Modifies the ``PushConfig`` for a specified subscription.

        This may be used to change a push subscription to a pull one
        (signified by an empty ``PushConfig``) or vice versa, or change
        the endpoint URL and other attributes of a push subscription.
        Messages will accumulate for delivery continuously through the
        call regardless of changes to the ``PushConfig``.

        Returns:
            Callable[[~.ModifyPushConfigRequest],
                    ~.Empty]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "modify_push_config" not in self._stubs:
            self._stubs["modify_push_config"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/ModifyPushConfig",
                request_serializer=pubsub.ModifyPushConfigRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs["modify_push_config"]

    @property
    def get_snapshot(self) -> Callable[[pubsub.GetSnapshotRequest], pubsub.Snapshot]:
        r"""Return a callable for the get snapshot method over gRPC.

        Gets the configuration details of a snapshot. Snapshots are used
        in
        `Seek <https://cloud.google.com/pubsub/docs/replay-overview>`__
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.

        Returns:
            Callable[[~.GetSnapshotRequest],
                    ~.Snapshot]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "get_snapshot" not in self._stubs:
            self._stubs["get_snapshot"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/GetSnapshot",
                request_serializer=pubsub.GetSnapshotRequest.serialize,
                response_deserializer=pubsub.Snapshot.deserialize,
            )
        return self._stubs["get_snapshot"]

    @property
    def list_snapshots(
        self,
    ) -> Callable[[pubsub.ListSnapshotsRequest], pubsub.ListSnapshotsResponse]:
        r"""Return a callable for the list snapshots method over gRPC.

        Lists the existing snapshots. Snapshots are used in
        `Seek <https://cloud.google.com/pubsub/docs/replay-overview>`__
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.

        Returns:
            Callable[[~.ListSnapshotsRequest],
                    ~.ListSnapshotsResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "list_snapshots" not in self._stubs:
            self._stubs["list_snapshots"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/ListSnapshots",
                request_serializer=pubsub.ListSnapshotsRequest.serialize,
                response_deserializer=pubsub.ListSnapshotsResponse.deserialize,
            )
        return self._stubs["list_snapshots"]

    @property
    def create_snapshot(
        self,
    ) -> Callable[[pubsub.CreateSnapshotRequest], pubsub.Snapshot]:
        r"""Return a callable for the create snapshot method over gRPC.

        Creates a snapshot from the requested subscription. Snapshots
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

        Returns:
            Callable[[~.CreateSnapshotRequest],
                    ~.Snapshot]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "create_snapshot" not in self._stubs:
            self._stubs["create_snapshot"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/CreateSnapshot",
                request_serializer=pubsub.CreateSnapshotRequest.serialize,
                response_deserializer=pubsub.Snapshot.deserialize,
            )
        return self._stubs["create_snapshot"]

    @property
    def update_snapshot(
        self,
    ) -> Callable[[pubsub.UpdateSnapshotRequest], pubsub.Snapshot]:
        r"""Return a callable for the update snapshot method over gRPC.

        Updates an existing snapshot. Snapshots are used in
        `Seek <https://cloud.google.com/pubsub/docs/replay-overview>`__
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.

        Returns:
            Callable[[~.UpdateSnapshotRequest],
                    ~.Snapshot]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "update_snapshot" not in self._stubs:
            self._stubs["update_snapshot"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/UpdateSnapshot",
                request_serializer=pubsub.UpdateSnapshotRequest.serialize,
                response_deserializer=pubsub.Snapshot.deserialize,
            )
        return self._stubs["update_snapshot"]

    @property
    def delete_snapshot(
        self,
    ) -> Callable[[pubsub.DeleteSnapshotRequest], empty_pb2.Empty]:
        r"""Return a callable for the delete snapshot method over gRPC.

        Removes an existing snapshot. Snapshots are used in [Seek]
        (https://cloud.google.com/pubsub/docs/replay-overview)
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.
        When the snapshot is deleted, all messages retained in the
        snapshot are immediately dropped. After a snapshot is deleted, a
        new one may be created with the same name, but the new one has
        no association with the old snapshot or its subscription, unless
        the same subscription is specified.

        Returns:
            Callable[[~.DeleteSnapshotRequest],
                    ~.Empty]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "delete_snapshot" not in self._stubs:
            self._stubs["delete_snapshot"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/DeleteSnapshot",
                request_serializer=pubsub.DeleteSnapshotRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs["delete_snapshot"]

    @property
    def seek(self) -> Callable[[pubsub.SeekRequest], pubsub.SeekResponse]:
        r"""Return a callable for the seek method over gRPC.

        Seeks an existing subscription to a point in time or to a given
        snapshot, whichever is provided in the request. Snapshots are
        used in [Seek]
        (https://cloud.google.com/pubsub/docs/replay-overview)
        operations, which allow you to manage message acknowledgments in
        bulk. That is, you can set the acknowledgment state of messages
        in an existing subscription to the state captured by a snapshot.
        Note that both the subscription and the snapshot must be on the
        same topic.

        Returns:
            Callable[[~.SeekRequest],
                    ~.SeekResponse]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "seek" not in self._stubs:
            self._stubs["seek"] = self.grpc_channel.unary_unary(
                "/google.pubsub.v1.Subscriber/Seek",
                request_serializer=pubsub.SeekRequest.serialize,
                response_deserializer=pubsub.SeekResponse.deserialize,
            )
        return self._stubs["seek"]

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


__all__ = ("SubscriberGrpcTransport",)
