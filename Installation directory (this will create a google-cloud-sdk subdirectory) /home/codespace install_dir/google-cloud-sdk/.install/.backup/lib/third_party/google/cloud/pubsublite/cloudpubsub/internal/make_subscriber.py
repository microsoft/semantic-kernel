# Copyright 2020 Google LLC
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

from typing import Optional, Mapping, Set, AsyncIterator, Callable
from uuid import uuid4

from google.api_core.client_options import ClientOptions
from google.auth.credentials import Credentials

from google.cloud.pubsublite.cloudpubsub.reassignment_handler import (
    ReassignmentHandler,
    DefaultReassignmentHandler,
)
from google.cloud.pubsublite.cloudpubsub.message_transforms import (
    to_cps_subscribe_message,
    add_id_to_cps_subscribe_transformer,
)
from google.cloud.pubsublite.internal.wire.client_cache import ClientCache
from google.cloud.pubsublite.types import FlowControlSettings
from google.cloud.pubsublite.cloudpubsub.internal.ack_set_tracker_impl import (
    AckSetTrackerImpl,
)
from google.cloud.pubsublite.cloudpubsub.internal.assigning_subscriber import (
    PartitionSubscriberFactory,
    AssigningSingleSubscriber,
)
from google.cloud.pubsublite.cloudpubsub.internal.single_partition_subscriber import (
    SinglePartitionSingleSubscriber,
)
from google.cloud.pubsublite.cloudpubsub.message_transformer import MessageTransformer
from google.cloud.pubsublite.cloudpubsub.nack_handler import (
    NackHandler,
    DefaultNackHandler,
)
from google.cloud.pubsublite.cloudpubsub.internal.single_subscriber import (
    AsyncSingleSubscriber,
)
from google.cloud.pubsublite.internal.endpoints import regional_endpoint
from google.cloud.pubsublite.internal.wire.assigner import Assigner
from google.cloud.pubsublite.internal.wire.assigner_impl import AssignerImpl
from google.cloud.pubsublite.internal.wire.committer_impl import CommitterImpl
from google.cloud.pubsublite.internal.wire.fixed_set_assigner import FixedSetAssigner
from google.cloud.pubsublite.internal.wire.gapic_connection import (
    GapicConnectionFactory,
)
from google.cloud.pubsublite.internal.wire.merge_metadata import merge_metadata
from google.cloud.pubsublite.internal.wire.pubsub_context import pubsub_context
import google.cloud.pubsublite.internal.wire.subscriber_impl as wire_subscriber
from google.cloud.pubsublite.internal.wire.subscriber_reset_handler import (
    SubscriberResetHandler,
)
from google.cloud.pubsublite.types import Partition, SubscriptionPath
from google.cloud.pubsublite.internal.routing_metadata import (
    subscription_routing_metadata,
)
from google.cloud.pubsublite_v1 import (
    SubscribeRequest,
    InitialSubscribeRequest,
    StreamingCommitCursorRequest,
    PartitionAssignmentRequest,
    InitialPartitionAssignmentRequest,
    InitialCommitCursorRequest,
)
from google.cloud.pubsublite_v1.services.subscriber_service.async_client import (
    SubscriberServiceAsyncClient,
)
from google.cloud.pubsublite_v1.services.partition_assignment_service.async_client import (
    PartitionAssignmentServiceAsyncClient,
)
from google.cloud.pubsublite_v1.services.cursor_service.async_client import (
    CursorServiceAsyncClient,
)

_DEFAULT_FLUSH_SECONDS = 0.1


def _make_dynamic_assigner(
    subscription: SubscriptionPath,
    transport: str,
    client_options: ClientOptions,
    credentials: Optional[Credentials],
    base_metadata: Optional[Mapping[str, str]],
) -> Assigner:
    if base_metadata is None:
        base_metadata = {}

    def assignment_connection_factory(
        requests: AsyncIterator[PartitionAssignmentRequest],
    ):
        assignment_client = PartitionAssignmentServiceAsyncClient(credentials=credentials, transport=transport, client_options=client_options)  # type: ignore
        return assignment_client.assign_partitions(
            requests, metadata=list(base_metadata.items())
        )

    return AssignerImpl(
        InitialPartitionAssignmentRequest(
            subscription=str(subscription), client_id=uuid4().bytes
        ),
        GapicConnectionFactory(assignment_connection_factory),
    )


def _make_partition_subscriber_factory(
    subscription: SubscriptionPath,
    transport: str,
    client_options: ClientOptions,
    credentials: Optional[Credentials],
    base_metadata: Optional[Mapping[str, str]],
    flow_control_settings: FlowControlSettings,
    nack_handler: NackHandler,
    message_transformer: MessageTransformer,
) -> PartitionSubscriberFactory:
    subscribe_client_cache = ClientCache(
        lambda: SubscriberServiceAsyncClient(
            credentials=credentials, transport=transport, client_options=client_options
        )
    )
    cursor_client_cache = ClientCache(
        lambda: CursorServiceAsyncClient(
            credentials=credentials, transport=transport, client_options=client_options
        )
    )

    def factory(partition: Partition) -> AsyncSingleSubscriber:
        final_metadata = merge_metadata(
            base_metadata, subscription_routing_metadata(subscription, partition)
        )

        def subscribe_connection_factory(requests: AsyncIterator[SubscribeRequest]):
            return subscribe_client_cache.get().subscribe(
                requests, metadata=list(final_metadata.items())
            )

        def cursor_connection_factory(
            requests: AsyncIterator[StreamingCommitCursorRequest],
        ):
            return cursor_client_cache.get().streaming_commit_cursor(
                requests, metadata=list(final_metadata.items())
            )

        def subscriber_factory(reset_handler: SubscriberResetHandler):
            return wire_subscriber.SubscriberImpl(
                InitialSubscribeRequest(
                    subscription=str(subscription), partition=partition.value
                ),
                _DEFAULT_FLUSH_SECONDS,
                GapicConnectionFactory(subscribe_connection_factory),
                reset_handler,
            )

        committer = CommitterImpl(
            InitialCommitCursorRequest(
                subscription=str(subscription), partition=partition.value
            ),
            _DEFAULT_FLUSH_SECONDS,
            GapicConnectionFactory(cursor_connection_factory),
        )
        ack_set_tracker = AckSetTrackerImpl(committer)
        return SinglePartitionSingleSubscriber(
            subscriber_factory,
            flow_control_settings,
            ack_set_tracker,
            nack_handler,
            add_id_to_cps_subscribe_transformer(partition, message_transformer),
        )

    return factory


def make_async_subscriber(
    subscription: SubscriptionPath,
    transport: str,
    per_partition_flow_control_settings: FlowControlSettings,
    nack_handler: Optional[NackHandler] = None,
    reassignment_handler: Optional[ReassignmentHandler] = None,
    message_transformer: Optional[MessageTransformer] = None,
    fixed_partitions: Optional[Set[Partition]] = None,
    credentials: Optional[Credentials] = None,
    client_options: Optional[ClientOptions] = None,
    metadata: Optional[Mapping[str, str]] = None,
) -> AsyncSingleSubscriber:
    """
    Make a Pub/Sub Lite AsyncSubscriber.

    Args:
      subscription: The subscription to subscribe to.
      transport: The transport type to use.
      per_partition_flow_control_settings: The flow control settings for each partition subscribed to. Note that these
        settings apply to each partition individually, not in aggregate.
      nack_handler: An optional handler for when nack() is called on a Message. The default will fail the client.
      message_transformer: An optional transformer from Pub/Sub Lite messages to Cloud Pub/Sub messages.
      fixed_partitions: A fixed set of partitions to subscribe to. If not present, will instead use auto-assignment.
      credentials: The credentials to use to connect. GOOGLE_DEFAULT_CREDENTIALS is used if None.
      client_options: Other options to pass to the client. Note that if you pass any you must set api_endpoint.
      metadata: Additional metadata to send with the RPC.

    Returns:
      A new AsyncSubscriber.
    """
    metadata = merge_metadata(pubsub_context(framework="CLOUD_PUBSUB_SHIM"), metadata)
    if client_options is None:
        client_options = ClientOptions(
            api_endpoint=regional_endpoint(subscription.location.region)
        )
    assigner_factory: Callable[[], Assigner]
    if fixed_partitions:
        assigner_factory = lambda: FixedSetAssigner(fixed_partitions)  # noqa: E731
    else:
        assigner_factory = lambda: _make_dynamic_assigner(  # noqa: E731
            subscription,
            transport,
            client_options,
            credentials,
            metadata,
        )

    if nack_handler is None:
        nack_handler = DefaultNackHandler()
    if reassignment_handler is None:
        reassignment_handler = DefaultReassignmentHandler()
    if message_transformer is None:
        message_transformer = MessageTransformer.of_callable(to_cps_subscribe_message)
    partition_subscriber_factory = _make_partition_subscriber_factory(
        subscription,
        transport,
        client_options,
        credentials,
        metadata,
        per_partition_flow_control_settings,
        nack_handler,
        message_transformer,
    )
    return AssigningSingleSubscriber(
        assigner_factory, partition_subscriber_factory, reassignment_handler
    )
