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

from abc import ABC, abstractmethod
from typing import List, Optional, Union

from google.api_core.operation import Operation
from google.cloud.pubsublite.types import (
    CloudRegion,
    TopicPath,
    LocationPath,
    SubscriptionPath,
    BacklogLocation,
    PublishTime,
    EventTime,
)
from google.cloud.pubsublite.types.paths import ReservationPath
from google.cloud.pubsublite_v1 import Topic, Subscription, Reservation
from cloudsdk.google.protobuf.field_mask_pb2 import FieldMask  # pytype: disable=pyi-error


class AdminClientInterface(ABC):
    """
    An admin client for Pub/Sub Lite. Only operates on a single region.
    """

    @abstractmethod
    def region(self) -> CloudRegion:
        """The region this client is for."""

    @abstractmethod
    def create_topic(self, topic: Topic) -> Topic:
        """Create a topic, returns the created topic."""

    @abstractmethod
    def get_topic(self, topic_path: TopicPath) -> Topic:
        """Get the topic object from the server."""

    @abstractmethod
    def get_topic_partition_count(self, topic_path: TopicPath) -> int:
        """Get the number of partitions in the provided topic."""

    @abstractmethod
    def list_topics(self, location_path: LocationPath) -> List[Topic]:
        """List the Pub/Sub lite topics that exist for a project in a given location."""

    @abstractmethod
    def update_topic(self, topic: Topic, update_mask: FieldMask) -> Topic:
        """Update the masked fields of the provided topic."""

    @abstractmethod
    def delete_topic(self, topic_path: TopicPath):
        """Delete a topic and all associated messages."""

    @abstractmethod
    def list_topic_subscriptions(self, topic_path: TopicPath) -> List[SubscriptionPath]:
        """List the subscriptions that exist for a given topic."""

    @abstractmethod
    def create_subscription(
        self,
        subscription: Subscription,
        target: Union[BacklogLocation, PublishTime, EventTime] = BacklogLocation.END,
        starting_offset: Optional[BacklogLocation] = None,
    ) -> Subscription:
        """Create a subscription, returns the created subscription. By default
        a subscription will only receive messages published after the
        subscription was created.

        `starting_offset` is deprecated. Use `target` to initialize the
        subscription to a target location within the message backlog instead.
        `starting_offset` has higher precedence if `target` is also set.

        A seek is initiated if the target location is a publish or event time.
        If the seek fails, the created subscription is not deleted.
        """

    @abstractmethod
    def get_subscription(self, subscription_path: SubscriptionPath) -> Subscription:
        """Get the subscription object from the server."""

    @abstractmethod
    def list_subscriptions(self, location_path: LocationPath) -> List[Subscription]:
        """List the Pub/Sub lite subscriptions that exist for a project in a given location."""

    @abstractmethod
    def update_subscription(
        self, subscription: Subscription, update_mask: FieldMask
    ) -> Subscription:
        """Update the masked fields of the provided subscription."""

    @abstractmethod
    def seek_subscription(
        self,
        subscription_path: SubscriptionPath,
        target: Union[BacklogLocation, PublishTime, EventTime],
    ) -> Operation:
        """Initiate an out-of-band seek for a subscription to a specified target.

        The seek target may be timestamps or named positions within the message
        backlog See https://cloud.google.com/pubsub/lite/docs/seek for more
        information.

        Returns:
            google.api_core.operation.Operation with:
              result type: google.cloud.pubsublite.SeekSubscriptionResponse
              metadata type: google.cloud.pubsublite.OperationMetadata
        """

    @abstractmethod
    def delete_subscription(self, subscription_path: SubscriptionPath):
        """Delete a subscription and all associated messages."""

    @abstractmethod
    def create_reservation(self, reservation: Reservation) -> Reservation:
        """Create a reservation, returns the created reservation."""

    @abstractmethod
    def get_reservation(self, reservation_path: ReservationPath) -> Reservation:
        """Get the reservation object from the server."""

    @abstractmethod
    def list_reservations(self, location_path: LocationPath) -> List[Reservation]:
        """List the Pub/Sub lite reservations that exist for a project in a given location."""

    @abstractmethod
    def update_reservation(
        self, reservation: Reservation, update_mask: FieldMask
    ) -> Reservation:
        """Update the masked fields of the provided reservation."""

    @abstractmethod
    def delete_reservation(self, reservation_path: ReservationPath):
        """Delete a reservation and all associated messages."""

    @abstractmethod
    def list_reservation_topics(
        self, reservation_path: ReservationPath
    ) -> List[TopicPath]:
        """List the subscriptions that exist for a given reservation."""
