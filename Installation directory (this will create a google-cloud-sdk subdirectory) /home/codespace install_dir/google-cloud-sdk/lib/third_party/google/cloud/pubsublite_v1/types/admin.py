# -*- coding: utf-8 -*-
# Copyright 2022 Google LLC
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
from __future__ import annotations

from typing import MutableMapping, MutableSequence

import proto  # type: ignore

from google.cloud.pubsublite_v1.types import common
from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore


__protobuf__ = proto.module(
    package="google.cloud.pubsublite.v1",
    manifest={
        "CreateTopicRequest",
        "GetTopicRequest",
        "GetTopicPartitionsRequest",
        "TopicPartitions",
        "ListTopicsRequest",
        "ListTopicsResponse",
        "UpdateTopicRequest",
        "DeleteTopicRequest",
        "ListTopicSubscriptionsRequest",
        "ListTopicSubscriptionsResponse",
        "CreateSubscriptionRequest",
        "GetSubscriptionRequest",
        "ListSubscriptionsRequest",
        "ListSubscriptionsResponse",
        "UpdateSubscriptionRequest",
        "DeleteSubscriptionRequest",
        "SeekSubscriptionRequest",
        "SeekSubscriptionResponse",
        "OperationMetadata",
        "CreateReservationRequest",
        "GetReservationRequest",
        "ListReservationsRequest",
        "ListReservationsResponse",
        "UpdateReservationRequest",
        "DeleteReservationRequest",
        "ListReservationTopicsRequest",
        "ListReservationTopicsResponse",
    },
)


class CreateTopicRequest(proto.Message):
    r"""Request for CreateTopic.

    Attributes:
        parent (str):
            Required. The parent location in which to create the topic.
            Structured like
            ``projects/{project_number}/locations/{location}``.
        topic (google.cloud.pubsublite_v1.types.Topic):
            Required. Configuration of the topic to create. Its ``name``
            field is ignored.
        topic_id (str):
            Required. The ID to use for the topic, which will become the
            final component of the topic's name.

            This value is structured like: ``my-topic-name``.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    topic: common.Topic = proto.Field(
        proto.MESSAGE,
        number=2,
        message=common.Topic,
    )
    topic_id: str = proto.Field(
        proto.STRING,
        number=3,
    )


class GetTopicRequest(proto.Message):
    r"""Request for GetTopic.

    Attributes:
        name (str):
            Required. The name of the topic whose
            configuration to return.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class GetTopicPartitionsRequest(proto.Message):
    r"""Request for GetTopicPartitions.

    Attributes:
        name (str):
            Required. The topic whose partition
            information to return.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class TopicPartitions(proto.Message):
    r"""Response for GetTopicPartitions.

    Attributes:
        partition_count (int):
            The number of partitions in the topic.
    """

    partition_count: int = proto.Field(
        proto.INT64,
        number=1,
    )


class ListTopicsRequest(proto.Message):
    r"""Request for ListTopics.

    Attributes:
        parent (str):
            Required. The parent whose topics are to be listed.
            Structured like
            ``projects/{project_number}/locations/{location}``.
        page_size (int):
            The maximum number of topics to return. The
            service may return fewer than this value.
            If unset or zero, all topics for the parent will
            be returned.
        page_token (str):
            A page token, received from a previous ``ListTopics`` call.
            Provide this to retrieve the subsequent page.

            When paginating, all other parameters provided to
            ``ListTopics`` must match the call that provided the page
            token.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )


class ListTopicsResponse(proto.Message):
    r"""Response for ListTopics.

    Attributes:
        topics (MutableSequence[google.cloud.pubsublite_v1.types.Topic]):
            The list of topic in the requested parent.
            The order of the topics is unspecified.
        next_page_token (str):
            A token that can be sent as ``page_token`` to retrieve the
            next page of results. If this field is omitted, there are no
            more results.
    """

    @property
    def raw_page(self):
        return self

    topics: MutableSequence[common.Topic] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message=common.Topic,
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class UpdateTopicRequest(proto.Message):
    r"""Request for UpdateTopic.

    Attributes:
        topic (google.cloud.pubsublite_v1.types.Topic):
            Required. The topic to update. Its ``name`` field must be
            populated.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. A mask specifying the topic fields
            to change.
    """

    topic: common.Topic = proto.Field(
        proto.MESSAGE,
        number=1,
        message=common.Topic,
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=2,
        message=field_mask_pb2.FieldMask,
    )


class DeleteTopicRequest(proto.Message):
    r"""Request for DeleteTopic.

    Attributes:
        name (str):
            Required. The name of the topic to delete.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListTopicSubscriptionsRequest(proto.Message):
    r"""Request for ListTopicSubscriptions.

    Attributes:
        name (str):
            Required. The name of the topic whose
            subscriptions to list.
        page_size (int):
            The maximum number of subscriptions to
            return. The service may return fewer than this
            value. If unset or zero, all subscriptions for
            the given topic will be returned.
        page_token (str):
            A page token, received from a previous
            ``ListTopicSubscriptions`` call. Provide this to retrieve
            the subsequent page.

            When paginating, all other parameters provided to
            ``ListTopicSubscriptions`` must match the call that provided
            the page token.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )


class ListTopicSubscriptionsResponse(proto.Message):
    r"""Response for ListTopicSubscriptions.

    Attributes:
        subscriptions (MutableSequence[str]):
            The names of subscriptions attached to the
            topic. The order of the subscriptions is
            unspecified.
        next_page_token (str):
            A token that can be sent as ``page_token`` to retrieve the
            next page of results. If this field is omitted, there are no
            more results.
    """

    @property
    def raw_page(self):
        return self

    subscriptions: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=1,
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class CreateSubscriptionRequest(proto.Message):
    r"""Request for CreateSubscription.

    Attributes:
        parent (str):
            Required. The parent location in which to create the
            subscription. Structured like
            ``projects/{project_number}/locations/{location}``.
        subscription (google.cloud.pubsublite_v1.types.Subscription):
            Required. Configuration of the subscription to create. Its
            ``name`` field is ignored.
        subscription_id (str):
            Required. The ID to use for the subscription, which will
            become the final component of the subscription's name.

            This value is structured like: ``my-sub-name``.
        skip_backlog (bool):
            If true, the newly created subscription will
            only receive messages published after the
            subscription was created. Otherwise, the entire
            message backlog will be received on the
            subscription. Defaults to false.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    subscription: common.Subscription = proto.Field(
        proto.MESSAGE,
        number=2,
        message=common.Subscription,
    )
    subscription_id: str = proto.Field(
        proto.STRING,
        number=3,
    )
    skip_backlog: bool = proto.Field(
        proto.BOOL,
        number=4,
    )


class GetSubscriptionRequest(proto.Message):
    r"""Request for GetSubscription.

    Attributes:
        name (str):
            Required. The name of the subscription whose
            configuration to return.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListSubscriptionsRequest(proto.Message):
    r"""Request for ListSubscriptions.

    Attributes:
        parent (str):
            Required. The parent whose subscriptions are to be listed.
            Structured like
            ``projects/{project_number}/locations/{location}``.
        page_size (int):
            The maximum number of subscriptions to
            return. The service may return fewer than this
            value. If unset or zero, all subscriptions for
            the parent will be returned.
        page_token (str):
            A page token, received from a previous ``ListSubscriptions``
            call. Provide this to retrieve the subsequent page.

            When paginating, all other parameters provided to
            ``ListSubscriptions`` must match the call that provided the
            page token.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )


class ListSubscriptionsResponse(proto.Message):
    r"""Response for ListSubscriptions.

    Attributes:
        subscriptions (MutableSequence[google.cloud.pubsublite_v1.types.Subscription]):
            The list of subscriptions in the requested
            parent. The order of the subscriptions is
            unspecified.
        next_page_token (str):
            A token that can be sent as ``page_token`` to retrieve the
            next page of results. If this field is omitted, there are no
            more results.
    """

    @property
    def raw_page(self):
        return self

    subscriptions: MutableSequence[common.Subscription] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message=common.Subscription,
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class UpdateSubscriptionRequest(proto.Message):
    r"""Request for UpdateSubscription.

    Attributes:
        subscription (google.cloud.pubsublite_v1.types.Subscription):
            Required. The subscription to update. Its ``name`` field
            must be populated. Topic field must not be populated.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. A mask specifying the subscription
            fields to change.
    """

    subscription: common.Subscription = proto.Field(
        proto.MESSAGE,
        number=1,
        message=common.Subscription,
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=2,
        message=field_mask_pb2.FieldMask,
    )


class DeleteSubscriptionRequest(proto.Message):
    r"""Request for DeleteSubscription.

    Attributes:
        name (str):
            Required. The name of the subscription to
            delete.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class SeekSubscriptionRequest(proto.Message):
    r"""Request for SeekSubscription.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        name (str):
            Required. The name of the subscription to
            seek.
        named_target (google.cloud.pubsublite_v1.types.SeekSubscriptionRequest.NamedTarget):
            Seek to a named position with respect to the
            message backlog.

            This field is a member of `oneof`_ ``target``.
        time_target (google.cloud.pubsublite_v1.types.TimeTarget):
            Seek to the first message whose publish or
            event time is greater than or equal to the
            specified query time. If no such message can be
            located, will seek to the end of the message
            backlog.

            This field is a member of `oneof`_ ``target``.
    """

    class NamedTarget(proto.Enum):
        r"""A named position with respect to the message backlog.

        Values:
            NAMED_TARGET_UNSPECIFIED (0):
                Unspecified named target. Do not use.
            TAIL (1):
                Seek to the oldest retained message.
            HEAD (2):
                Seek past all recently published messages,
                skipping the entire message backlog.
        """
        NAMED_TARGET_UNSPECIFIED = 0
        TAIL = 1
        HEAD = 2

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    named_target: NamedTarget = proto.Field(
        proto.ENUM,
        number=2,
        oneof="target",
        enum=NamedTarget,
    )
    time_target: common.TimeTarget = proto.Field(
        proto.MESSAGE,
        number=3,
        oneof="target",
        message=common.TimeTarget,
    )


class SeekSubscriptionResponse(proto.Message):
    r"""Response for SeekSubscription long running operation."""


class OperationMetadata(proto.Message):
    r"""Metadata for long running operations.

    Attributes:
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            The time the operation was created.
        end_time (google.protobuf.timestamp_pb2.Timestamp):
            The time the operation finished running. Not
            set if the operation has not completed.
        target (str):
            Resource path for the target of the operation. For example,
            targets of seeks are subscription resources, structured
            like:
            projects/{project_number}/locations/{location}/subscriptions/{subscription_id}
        verb (str):
            Name of the verb executed by the operation.
    """

    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=1,
        message=timestamp_pb2.Timestamp,
    )
    end_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=2,
        message=timestamp_pb2.Timestamp,
    )
    target: str = proto.Field(
        proto.STRING,
        number=3,
    )
    verb: str = proto.Field(
        proto.STRING,
        number=4,
    )


class CreateReservationRequest(proto.Message):
    r"""Request for CreateReservation.

    Attributes:
        parent (str):
            Required. The parent location in which to create the
            reservation. Structured like
            ``projects/{project_number}/locations/{location}``.
        reservation (google.cloud.pubsublite_v1.types.Reservation):
            Required. Configuration of the reservation to create. Its
            ``name`` field is ignored.
        reservation_id (str):
            Required. The ID to use for the reservation, which will
            become the final component of the reservation's name.

            This value is structured like: ``my-reservation-name``.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    reservation: common.Reservation = proto.Field(
        proto.MESSAGE,
        number=2,
        message=common.Reservation,
    )
    reservation_id: str = proto.Field(
        proto.STRING,
        number=3,
    )


class GetReservationRequest(proto.Message):
    r"""Request for GetReservation.

    Attributes:
        name (str):
            Required. The name of the reservation whose configuration to
            return. Structured like:
            projects/{project_number}/locations/{location}/reservations/{reservation_id}
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListReservationsRequest(proto.Message):
    r"""Request for ListReservations.

    Attributes:
        parent (str):
            Required. The parent whose reservations are to be listed.
            Structured like
            ``projects/{project_number}/locations/{location}``.
        page_size (int):
            The maximum number of reservations to return.
            The service may return fewer than this value. If
            unset or zero, all reservations for the parent
            will be returned.
        page_token (str):
            A page token, received from a previous ``ListReservations``
            call. Provide this to retrieve the subsequent page.

            When paginating, all other parameters provided to
            ``ListReservations`` must match the call that provided the
            page token.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )


class ListReservationsResponse(proto.Message):
    r"""Response for ListReservations.

    Attributes:
        reservations (MutableSequence[google.cloud.pubsublite_v1.types.Reservation]):
            The list of reservation in the requested
            parent. The order of the reservations is
            unspecified.
        next_page_token (str):
            A token that can be sent as ``page_token`` to retrieve the
            next page of results. If this field is omitted, there are no
            more results.
    """

    @property
    def raw_page(self):
        return self

    reservations: MutableSequence[common.Reservation] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message=common.Reservation,
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class UpdateReservationRequest(proto.Message):
    r"""Request for UpdateReservation.

    Attributes:
        reservation (google.cloud.pubsublite_v1.types.Reservation):
            Required. The reservation to update. Its ``name`` field must
            be populated.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. A mask specifying the reservation
            fields to change.
    """

    reservation: common.Reservation = proto.Field(
        proto.MESSAGE,
        number=1,
        message=common.Reservation,
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=2,
        message=field_mask_pb2.FieldMask,
    )


class DeleteReservationRequest(proto.Message):
    r"""Request for DeleteReservation.

    Attributes:
        name (str):
            Required. The name of the reservation to delete. Structured
            like:
            projects/{project_number}/locations/{location}/reservations/{reservation_id}
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListReservationTopicsRequest(proto.Message):
    r"""Request for ListReservationTopics.

    Attributes:
        name (str):
            Required. The name of the reservation whose topics to list.
            Structured like:
            projects/{project_number}/locations/{location}/reservations/{reservation_id}
        page_size (int):
            The maximum number of topics to return. The
            service may return fewer than this value.
            If unset or zero, all topics for the given
            reservation will be returned.
        page_token (str):
            A page token, received from a previous
            ``ListReservationTopics`` call. Provide this to retrieve the
            subsequent page.

            When paginating, all other parameters provided to
            ``ListReservationTopics`` must match the call that provided
            the page token.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )


class ListReservationTopicsResponse(proto.Message):
    r"""Response for ListReservationTopics.

    Attributes:
        topics (MutableSequence[str]):
            The names of topics attached to the
            reservation. The order of the topics is
            unspecified.
        next_page_token (str):
            A token that can be sent as ``page_token`` to retrieve the
            next page of results. If this field is omitted, there are no
            more results.
    """

    @property
    def raw_page(self):
        return self

    topics: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=1,
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


__all__ = tuple(sorted(__protobuf__.manifest))
