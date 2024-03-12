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

from typing import AsyncIterator, Mapping, Optional

from google.cloud.pubsub_v1.types import BatchSettings

from google.cloud.pubsublite.admin_client import AdminClient
from google.cloud.pubsublite.internal.endpoints import regional_endpoint
from google.cloud.pubsublite.internal.publisher_client_id import PublisherClientId
from google.cloud.pubsublite.internal.publish_sequence_number import (
    PublishSequenceNumber,
)
from google.cloud.pubsublite.internal.wire.client_cache import ClientCache
from google.cloud.pubsublite.internal.wire.default_routing_policy import (
    DefaultRoutingPolicy,
)
from google.cloud.pubsublite.internal.wire.gapic_connection import (
    GapicConnectionFactory,
)
from google.cloud.pubsublite.internal.wire.merge_metadata import merge_metadata
from google.cloud.pubsublite.internal.wire.partition_count_watcher_impl import (
    PartitionCountWatcherImpl,
)
from google.cloud.pubsublite.internal.wire.partition_count_watching_publisher import (
    PartitionCountWatchingPublisher,
)
from google.cloud.pubsublite.internal.wire.publisher import Publisher
from google.cloud.pubsublite.internal.wire.single_partition_publisher import (
    SinglePartitionPublisher,
)
from google.cloud.pubsublite.types import Partition, TopicPath
from google.cloud.pubsublite.internal.routing_metadata import topic_routing_metadata
from google.cloud.pubsublite_v1 import InitialPublishRequest, PublishRequest
from google.cloud.pubsublite_v1.services.publisher_service import async_client
from google.api_core.client_options import ClientOptions
from google.auth.credentials import Credentials

DEFAULT_BATCHING_SETTINGS = BatchSettings(
    max_bytes=(
        3 * 1024 * 1024
    ),  # 3 MiB to stay 1 MiB below GRPC's 4 MiB per-message limit.
    max_messages=1000,
    max_latency=0.05,  # 50 ms
)
DEFAULT_PARTITION_POLL_PERIOD = 600  # ten minutes


def make_publisher(
    topic: TopicPath,
    transport: str,
    per_partition_batching_settings: Optional[BatchSettings] = None,
    credentials: Optional[Credentials] = None,
    client_options: Optional[ClientOptions] = None,
    metadata: Optional[Mapping[str, str]] = None,
    client_id: Optional[PublisherClientId] = None,
) -> Publisher:
    """
    Make a new publisher for the given topic.

    Args:
      topic: The topic to publish to.
      transport: The transport type to use.
      per_partition_batching_settings: Settings for batching messages on each partition. The default is reasonable for most cases.
      credentials: The credentials to use to connect. GOOGLE_DEFAULT_CREDENTIALS is used if None.
      client_options: Other options to pass to the client. Note that if you pass any you must set api_endpoint.
      metadata: Additional metadata to send with the RPC.
      client_id: 128-bit unique client id. If set, enables publish idempotency for the session.

    Returns:
      A new Publisher.

    Throws:
      GoogleApiCallException on any error determining topic structure.
    """
    if per_partition_batching_settings is None:
        per_partition_batching_settings = DEFAULT_BATCHING_SETTINGS
    admin_client = AdminClient(
        region=topic.location.region,
        credentials=credentials,
        client_options=client_options,
    )
    if client_options is None:
        client_options = ClientOptions(
            api_endpoint=regional_endpoint(topic.location.region)
        )
    client_cache = ClientCache(
        lambda: async_client.PublisherServiceAsyncClient(
            credentials=credentials, transport=transport, client_options=client_options
        )
    )

    def publisher_factory(partition: Partition):
        def connection_factory(requests: AsyncIterator[PublishRequest]):
            final_metadata = merge_metadata(
                metadata, topic_routing_metadata(topic, partition)
            )
            return client_cache.get().publish(
                requests, metadata=list(final_metadata.items())
            )

        initial_request = InitialPublishRequest(
            topic=str(topic), partition=partition.value
        )
        if client_id:
            initial_request.client_id = client_id.value
        return SinglePartitionPublisher(
            initial_request,
            per_partition_batching_settings,
            GapicConnectionFactory(connection_factory),
            PublishSequenceNumber(0),
        )

    def policy_factory(partition_count: int):
        return DefaultRoutingPolicy(partition_count)

    return PartitionCountWatchingPublisher(
        PartitionCountWatcherImpl(admin_client, topic, DEFAULT_PARTITION_POLL_PERIOD),
        publisher_factory,
        policy_factory,
    )
