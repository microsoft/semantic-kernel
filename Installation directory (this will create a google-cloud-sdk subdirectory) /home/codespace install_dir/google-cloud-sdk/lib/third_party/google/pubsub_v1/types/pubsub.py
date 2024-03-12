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
from __future__ import annotations

from typing import MutableMapping, MutableSequence

import proto  # type: ignore

from cloudsdk.google.protobuf import duration_pb2  # type: ignore
from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore
from google.pubsub_v1.types import schema as gp_schema


__protobuf__ = proto.module(
    package="google.pubsub.v1",
    manifest={
        "MessageStoragePolicy",
        "SchemaSettings",
        "Topic",
        "PubsubMessage",
        "GetTopicRequest",
        "UpdateTopicRequest",
        "PublishRequest",
        "PublishResponse",
        "ListTopicsRequest",
        "ListTopicsResponse",
        "ListTopicSubscriptionsRequest",
        "ListTopicSubscriptionsResponse",
        "ListTopicSnapshotsRequest",
        "ListTopicSnapshotsResponse",
        "DeleteTopicRequest",
        "DetachSubscriptionRequest",
        "DetachSubscriptionResponse",
        "Subscription",
        "RetryPolicy",
        "DeadLetterPolicy",
        "ExpirationPolicy",
        "PushConfig",
        "BigQueryConfig",
        "CloudStorageConfig",
        "ReceivedMessage",
        "GetSubscriptionRequest",
        "UpdateSubscriptionRequest",
        "ListSubscriptionsRequest",
        "ListSubscriptionsResponse",
        "DeleteSubscriptionRequest",
        "ModifyPushConfigRequest",
        "PullRequest",
        "PullResponse",
        "ModifyAckDeadlineRequest",
        "AcknowledgeRequest",
        "StreamingPullRequest",
        "StreamingPullResponse",
        "CreateSnapshotRequest",
        "UpdateSnapshotRequest",
        "Snapshot",
        "GetSnapshotRequest",
        "ListSnapshotsRequest",
        "ListSnapshotsResponse",
        "DeleteSnapshotRequest",
        "SeekRequest",
        "SeekResponse",
    },
)


class MessageStoragePolicy(proto.Message):
    r"""A policy constraining the storage of messages published to
    the topic.

    Attributes:
        allowed_persistence_regions (MutableSequence[str]):
            A list of IDs of GCP regions where messages
            that are published to the topic may be persisted
            in storage. Messages published by publishers
            running in non-allowed GCP regions (or running
            outside of GCP altogether) will be routed for
            storage in one of the allowed regions. An empty
            list means that no regions are allowed, and is
            not a valid configuration.
    """

    allowed_persistence_regions: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=1,
    )


class SchemaSettings(proto.Message):
    r"""Settings for validating messages published against a schema.

    Attributes:
        schema (str):
            Required. The name of the schema that messages published
            should be validated against. Format is
            ``projects/{project}/schemas/{schema}``. The value of this
            field will be ``_deleted-schema_`` if the schema has been
            deleted.
        encoding (google.pubsub_v1.types.Encoding):
            The encoding of messages validated against ``schema``.
        first_revision_id (str):
            The minimum (inclusive) revision allowed for validating
            messages. If empty or not present, allow any revision to be
            validated against last_revision or any revision created
            before.
        last_revision_id (str):
            The maximum (inclusive) revision allowed for validating
            messages. If empty or not present, allow any revision to be
            validated against first_revision or any revision created
            after.
    """

    schema: str = proto.Field(
        proto.STRING,
        number=1,
    )
    encoding: gp_schema.Encoding = proto.Field(
        proto.ENUM,
        number=2,
        enum=gp_schema.Encoding,
    )
    first_revision_id: str = proto.Field(
        proto.STRING,
        number=3,
    )
    last_revision_id: str = proto.Field(
        proto.STRING,
        number=4,
    )


class Topic(proto.Message):
    r"""A topic resource.

    Attributes:
        name (str):
            Required. The name of the topic. It must have the format
            ``"projects/{project}/topics/{topic}"``. ``{topic}`` must
            start with a letter, and contain only letters
            (``[A-Za-z]``), numbers (``[0-9]``), dashes (``-``),
            underscores (``_``), periods (``.``), tildes (``~``), plus
            (``+``) or percent signs (``%``). It must be between 3 and
            255 characters in length, and it must not start with
            ``"goog"``.
        labels (MutableMapping[str, str]):
            See [Creating and managing labels]
            (https://cloud.google.com/pubsub/docs/labels).
        message_storage_policy (google.pubsub_v1.types.MessageStoragePolicy):
            Policy constraining the set of Google Cloud
            Platform regions where messages published to the
            topic may be stored. If not present, then no
            constraints are in effect.
        kms_key_name (str):
            The resource name of the Cloud KMS CryptoKey to be used to
            protect access to messages published on this topic.

            The expected format is
            ``projects/*/locations/*/keyRings/*/cryptoKeys/*``.
        schema_settings (google.pubsub_v1.types.SchemaSettings):
            Settings for validating messages published
            against a schema.
        satisfies_pzs (bool):
            Reserved for future use. This field is set
            only in responses from the server; it is ignored
            if it is set in any requests.
        message_retention_duration (google.protobuf.duration_pb2.Duration):
            Indicates the minimum duration to retain a message after it
            is published to the topic. If this field is set, messages
            published to the topic in the last
            ``message_retention_duration`` are always available to
            subscribers. For instance, it allows any attached
            subscription to `seek to a
            timestamp <https://cloud.google.com/pubsub/docs/replay-overview#seek_to_a_time>`__
            that is up to ``message_retention_duration`` in the past. If
            this field is not set, message retention is controlled by
            settings on individual subscriptions. Cannot be more than 31
            days or less than 10 minutes.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    labels: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=2,
    )
    message_storage_policy: "MessageStoragePolicy" = proto.Field(
        proto.MESSAGE,
        number=3,
        message="MessageStoragePolicy",
    )
    kms_key_name: str = proto.Field(
        proto.STRING,
        number=5,
    )
    schema_settings: "SchemaSettings" = proto.Field(
        proto.MESSAGE,
        number=6,
        message="SchemaSettings",
    )
    satisfies_pzs: bool = proto.Field(
        proto.BOOL,
        number=7,
    )
    message_retention_duration: duration_pb2.Duration = proto.Field(
        proto.MESSAGE,
        number=8,
        message=duration_pb2.Duration,
    )


class PubsubMessage(proto.Message):
    r"""A message that is published by publishers and consumed by
    subscribers. The message must contain either a non-empty data field
    or at least one attribute. Note that client libraries represent this
    object differently depending on the language. See the corresponding
    `client library
    documentation <https://cloud.google.com/pubsub/docs/reference/libraries>`__
    for more information. See [quotas and limits]
    (https://cloud.google.com/pubsub/quotas) for more information about
    message limits.

    Attributes:
        data (bytes):
            The message data field. If this field is
            empty, the message must contain at least one
            attribute.
        attributes (MutableMapping[str, str]):
            Attributes for this message. If this field is
            empty, the message must contain non-empty data.
            This can be used to filter messages on the
            subscription.
        message_id (str):
            ID of this message, assigned by the server when the message
            is published. Guaranteed to be unique within the topic. This
            value may be read by a subscriber that receives a
            ``PubsubMessage`` via a ``Pull`` call or a push delivery. It
            must not be populated by the publisher in a ``Publish``
            call.
        publish_time (google.protobuf.timestamp_pb2.Timestamp):
            The time at which the message was published, populated by
            the server when it receives the ``Publish`` call. It must
            not be populated by the publisher in a ``Publish`` call.
        ordering_key (str):
            If non-empty, identifies related messages for which publish
            order should be respected. If a ``Subscription`` has
            ``enable_message_ordering`` set to ``true``, messages
            published with the same non-empty ``ordering_key`` value
            will be delivered to subscribers in the order in which they
            are received by the Pub/Sub system. All ``PubsubMessage``\ s
            published in a given ``PublishRequest`` must specify the
            same ``ordering_key`` value. For more information, see
            `ordering
            messages <https://cloud.google.com/pubsub/docs/ordering>`__.
    """

    data: bytes = proto.Field(
        proto.BYTES,
        number=1,
    )
    attributes: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=2,
    )
    message_id: str = proto.Field(
        proto.STRING,
        number=3,
    )
    publish_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=4,
        message=timestamp_pb2.Timestamp,
    )
    ordering_key: str = proto.Field(
        proto.STRING,
        number=5,
    )


class GetTopicRequest(proto.Message):
    r"""Request for the GetTopic method.

    Attributes:
        topic (str):
            Required. The name of the topic to get. Format is
            ``projects/{project}/topics/{topic}``.
    """

    topic: str = proto.Field(
        proto.STRING,
        number=1,
    )


class UpdateTopicRequest(proto.Message):
    r"""Request for the UpdateTopic method.

    Attributes:
        topic (google.pubsub_v1.types.Topic):
            Required. The updated topic object.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. Indicates which fields in the provided topic to
            update. Must be specified and non-empty. Note that if
            ``update_mask`` contains "message_storage_policy" but the
            ``message_storage_policy`` is not set in the ``topic``
            provided above, then the updated value is determined by the
            policy configured at the project or organization level.
    """

    topic: "Topic" = proto.Field(
        proto.MESSAGE,
        number=1,
        message="Topic",
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=2,
        message=field_mask_pb2.FieldMask,
    )


class PublishRequest(proto.Message):
    r"""Request for the Publish method.

    Attributes:
        topic (str):
            Required. The messages in the request will be published on
            this topic. Format is ``projects/{project}/topics/{topic}``.
        messages (MutableSequence[google.pubsub_v1.types.PubsubMessage]):
            Required. The messages to publish.
    """

    topic: str = proto.Field(
        proto.STRING,
        number=1,
    )
    messages: MutableSequence["PubsubMessage"] = proto.RepeatedField(
        proto.MESSAGE,
        number=2,
        message="PubsubMessage",
    )


class PublishResponse(proto.Message):
    r"""Response for the ``Publish`` method.

    Attributes:
        message_ids (MutableSequence[str]):
            The server-assigned ID of each published
            message, in the same order as the messages in
            the request. IDs are guaranteed to be unique
            within the topic.
    """

    message_ids: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=1,
    )


class ListTopicsRequest(proto.Message):
    r"""Request for the ``ListTopics`` method.

    Attributes:
        project (str):
            Required. The name of the project in which to list topics.
            Format is ``projects/{project-id}``.
        page_size (int):
            Maximum number of topics to return.
        page_token (str):
            The value returned by the last ``ListTopicsResponse``;
            indicates that this is a continuation of a prior
            ``ListTopics`` call, and that the system should return the
            next page of data.
    """

    project: str = proto.Field(
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
    r"""Response for the ``ListTopics`` method.

    Attributes:
        topics (MutableSequence[google.pubsub_v1.types.Topic]):
            The resulting topics.
        next_page_token (str):
            If not empty, indicates that there may be more topics that
            match the request; this value should be passed in a new
            ``ListTopicsRequest``.
    """

    @property
    def raw_page(self):
        return self

    topics: MutableSequence["Topic"] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message="Topic",
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class ListTopicSubscriptionsRequest(proto.Message):
    r"""Request for the ``ListTopicSubscriptions`` method.

    Attributes:
        topic (str):
            Required. The name of the topic that subscriptions are
            attached to. Format is
            ``projects/{project}/topics/{topic}``.
        page_size (int):
            Maximum number of subscription names to
            return.
        page_token (str):
            The value returned by the last
            ``ListTopicSubscriptionsResponse``; indicates that this is a
            continuation of a prior ``ListTopicSubscriptions`` call, and
            that the system should return the next page of data.
    """

    topic: str = proto.Field(
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
    r"""Response for the ``ListTopicSubscriptions`` method.

    Attributes:
        subscriptions (MutableSequence[str]):
            The names of subscriptions attached to the
            topic specified in the request.
        next_page_token (str):
            If not empty, indicates that there may be more subscriptions
            that match the request; this value should be passed in a new
            ``ListTopicSubscriptionsRequest`` to get more subscriptions.
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


class ListTopicSnapshotsRequest(proto.Message):
    r"""Request for the ``ListTopicSnapshots`` method.

    Attributes:
        topic (str):
            Required. The name of the topic that snapshots are attached
            to. Format is ``projects/{project}/topics/{topic}``.
        page_size (int):
            Maximum number of snapshot names to return.
        page_token (str):
            The value returned by the last
            ``ListTopicSnapshotsResponse``; indicates that this is a
            continuation of a prior ``ListTopicSnapshots`` call, and
            that the system should return the next page of data.
    """

    topic: str = proto.Field(
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


class ListTopicSnapshotsResponse(proto.Message):
    r"""Response for the ``ListTopicSnapshots`` method.

    Attributes:
        snapshots (MutableSequence[str]):
            The names of the snapshots that match the
            request.
        next_page_token (str):
            If not empty, indicates that there may be more snapshots
            that match the request; this value should be passed in a new
            ``ListTopicSnapshotsRequest`` to get more snapshots.
    """

    @property
    def raw_page(self):
        return self

    snapshots: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=1,
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class DeleteTopicRequest(proto.Message):
    r"""Request for the ``DeleteTopic`` method.

    Attributes:
        topic (str):
            Required. Name of the topic to delete. Format is
            ``projects/{project}/topics/{topic}``.
    """

    topic: str = proto.Field(
        proto.STRING,
        number=1,
    )


class DetachSubscriptionRequest(proto.Message):
    r"""Request for the DetachSubscription method.

    Attributes:
        subscription (str):
            Required. The subscription to detach. Format is
            ``projects/{project}/subscriptions/{subscription}``.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )


class DetachSubscriptionResponse(proto.Message):
    r"""Response for the DetachSubscription method.
    Reserved for future use.

    """


class Subscription(proto.Message):
    r"""A subscription resource. If none of ``push_config``,
    ``bigquery_config``, or ``cloud_storage_config`` is set, then the
    subscriber will pull and ack messages using API methods. At most one
    of these fields may be set.

    Attributes:
        name (str):
            Required. The name of the subscription. It must have the
            format
            ``"projects/{project}/subscriptions/{subscription}"``.
            ``{subscription}`` must start with a letter, and contain
            only letters (``[A-Za-z]``), numbers (``[0-9]``), dashes
            (``-``), underscores (``_``), periods (``.``), tildes
            (``~``), plus (``+``) or percent signs (``%``). It must be
            between 3 and 255 characters in length, and it must not
            start with ``"goog"``.
        topic (str):
            Required. The name of the topic from which this subscription
            is receiving messages. Format is
            ``projects/{project}/topics/{topic}``. The value of this
            field will be ``_deleted-topic_`` if the topic has been
            deleted.
        push_config (google.pubsub_v1.types.PushConfig):
            If push delivery is used with this
            subscription, this field is used to configure
            it.
        bigquery_config (google.pubsub_v1.types.BigQueryConfig):
            If delivery to BigQuery is used with this
            subscription, this field is used to configure
            it.
        cloud_storage_config (google.pubsub_v1.types.CloudStorageConfig):
            If delivery to Google Cloud Storage is used
            with this subscription, this field is used to
            configure it.
        ack_deadline_seconds (int):
            The approximate amount of time (on a best-effort basis)
            Pub/Sub waits for the subscriber to acknowledge receipt
            before resending the message. In the interval after the
            message is delivered and before it is acknowledged, it is
            considered to be *outstanding*. During that time period, the
            message will not be redelivered (on a best-effort basis).

            For pull subscriptions, this value is used as the initial
            value for the ack deadline. To override this value for a
            given message, call ``ModifyAckDeadline`` with the
            corresponding ``ack_id`` if using non-streaming pull or send
            the ``ack_id`` in a ``StreamingModifyAckDeadlineRequest`` if
            using streaming pull. The minimum custom deadline you can
            specify is 10 seconds. The maximum custom deadline you can
            specify is 600 seconds (10 minutes). If this parameter is 0,
            a default value of 10 seconds is used.

            For push delivery, this value is also used to set the
            request timeout for the call to the push endpoint.

            If the subscriber never acknowledges the message, the
            Pub/Sub system will eventually redeliver the message.
        retain_acked_messages (bool):
            Indicates whether to retain acknowledged messages. If true,
            then messages are not expunged from the subscription's
            backlog, even if they are acknowledged, until they fall out
            of the ``message_retention_duration`` window. This must be
            true if you would like to [``Seek`` to a timestamp]
            (https://cloud.google.com/pubsub/docs/replay-overview#seek_to_a_time)
            in the past to replay previously-acknowledged messages.
        message_retention_duration (google.protobuf.duration_pb2.Duration):
            How long to retain unacknowledged messages in the
            subscription's backlog, from the moment a message is
            published. If ``retain_acked_messages`` is true, then this
            also configures the retention of acknowledged messages, and
            thus configures how far back in time a ``Seek`` can be done.
            Defaults to 7 days. Cannot be more than 7 days or less than
            10 minutes.
        labels (MutableMapping[str, str]):
            See `Creating and managing
            labels <https://cloud.google.com/pubsub/docs/labels>`__.
        enable_message_ordering (bool):
            If true, messages published with the same ``ordering_key``
            in ``PubsubMessage`` will be delivered to the subscribers in
            the order in which they are received by the Pub/Sub system.
            Otherwise, they may be delivered in any order.
        expiration_policy (google.pubsub_v1.types.ExpirationPolicy):
            A policy that specifies the conditions for this
            subscription's expiration. A subscription is considered
            active as long as any connected subscriber is successfully
            consuming messages from the subscription or is issuing
            operations on the subscription. If ``expiration_policy`` is
            not set, a *default policy* with ``ttl`` of 31 days will be
            used. The minimum allowed value for
            ``expiration_policy.ttl`` is 1 day. If ``expiration_policy``
            is set, but ``expiration_policy.ttl`` is not set, the
            subscription never expires.
        filter (str):
            An expression written in the Pub/Sub `filter
            language <https://cloud.google.com/pubsub/docs/filtering>`__.
            If non-empty, then only ``PubsubMessage``\ s whose
            ``attributes`` field matches the filter are delivered on
            this subscription. If empty, then no messages are filtered
            out.
        dead_letter_policy (google.pubsub_v1.types.DeadLetterPolicy):
            A policy that specifies the conditions for dead lettering
            messages in this subscription. If dead_letter_policy is not
            set, dead lettering is disabled.

            The Cloud Pub/Sub service account associated with this
            subscriptions's parent project (i.e.,
            service-{project_number}@gcp-sa-pubsub.iam.gserviceaccount.com)
            must have permission to Acknowledge() messages on this
            subscription.
        retry_policy (google.pubsub_v1.types.RetryPolicy):
            A policy that specifies how Pub/Sub retries
            message delivery for this subscription.

            If not set, the default retry policy is applied.
            This generally implies that messages will be
            retried as soon as possible for healthy
            subscribers. RetryPolicy will be triggered on
            NACKs or acknowledgement deadline exceeded
            events for a given message.
        detached (bool):
            Indicates whether the subscription is detached from its
            topic. Detached subscriptions don't receive messages from
            their topic and don't retain any backlog. ``Pull`` and
            ``StreamingPull`` requests will return FAILED_PRECONDITION.
            If the subscription is a push subscription, pushes to the
            endpoint will not be made.
        enable_exactly_once_delivery (bool):
            If true, Pub/Sub provides the following guarantees for the
            delivery of a message with a given value of ``message_id``
            on this subscription:

            -  The message sent to a subscriber is guaranteed not to be
               resent before the message's acknowledgement deadline
               expires.
            -  An acknowledged message will not be resent to a
               subscriber.

            Note that subscribers may still receive multiple copies of a
            message when ``enable_exactly_once_delivery`` is true if the
            message was published multiple times by a publisher client.
            These copies are considered distinct by Pub/Sub and have
            distinct ``message_id`` values.
        topic_message_retention_duration (google.protobuf.duration_pb2.Duration):
            Output only. Indicates the minimum duration for which a
            message is retained after it is published to the
            subscription's topic. If this field is set, messages
            published to the subscription's topic in the last
            ``topic_message_retention_duration`` are always available to
            subscribers. See the ``message_retention_duration`` field in
            ``Topic``. This field is set only in responses from the
            server; it is ignored if it is set in any requests.
        state (google.pubsub_v1.types.Subscription.State):
            Output only. An output-only field indicating
            whether or not the subscription can receive
            messages.
    """

    class State(proto.Enum):
        r"""Possible states for a subscription.

        Values:
            STATE_UNSPECIFIED (0):
                Default value. This value is unused.
            ACTIVE (1):
                The subscription can actively receive
                messages
            RESOURCE_ERROR (2):
                The subscription cannot receive messages
                because of an error with the resource to which
                it pushes messages. See the more detailed error
                state in the corresponding configuration.
        """
        STATE_UNSPECIFIED = 0
        ACTIVE = 1
        RESOURCE_ERROR = 2

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    topic: str = proto.Field(
        proto.STRING,
        number=2,
    )
    push_config: "PushConfig" = proto.Field(
        proto.MESSAGE,
        number=4,
        message="PushConfig",
    )
    bigquery_config: "BigQueryConfig" = proto.Field(
        proto.MESSAGE,
        number=18,
        message="BigQueryConfig",
    )
    cloud_storage_config: "CloudStorageConfig" = proto.Field(
        proto.MESSAGE,
        number=22,
        message="CloudStorageConfig",
    )
    ack_deadline_seconds: int = proto.Field(
        proto.INT32,
        number=5,
    )
    retain_acked_messages: bool = proto.Field(
        proto.BOOL,
        number=7,
    )
    message_retention_duration: duration_pb2.Duration = proto.Field(
        proto.MESSAGE,
        number=8,
        message=duration_pb2.Duration,
    )
    labels: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=9,
    )
    enable_message_ordering: bool = proto.Field(
        proto.BOOL,
        number=10,
    )
    expiration_policy: "ExpirationPolicy" = proto.Field(
        proto.MESSAGE,
        number=11,
        message="ExpirationPolicy",
    )
    filter: str = proto.Field(
        proto.STRING,
        number=12,
    )
    dead_letter_policy: "DeadLetterPolicy" = proto.Field(
        proto.MESSAGE,
        number=13,
        message="DeadLetterPolicy",
    )
    retry_policy: "RetryPolicy" = proto.Field(
        proto.MESSAGE,
        number=14,
        message="RetryPolicy",
    )
    detached: bool = proto.Field(
        proto.BOOL,
        number=15,
    )
    enable_exactly_once_delivery: bool = proto.Field(
        proto.BOOL,
        number=16,
    )
    topic_message_retention_duration: duration_pb2.Duration = proto.Field(
        proto.MESSAGE,
        number=17,
        message=duration_pb2.Duration,
    )
    state: State = proto.Field(
        proto.ENUM,
        number=19,
        enum=State,
    )


class RetryPolicy(proto.Message):
    r"""A policy that specifies how Cloud Pub/Sub retries message delivery.

    Retry delay will be exponential based on provided minimum and
    maximum backoffs. https://en.wikipedia.org/wiki/Exponential_backoff.

    RetryPolicy will be triggered on NACKs or acknowledgement deadline
    exceeded events for a given message.

    Retry Policy is implemented on a best effort basis. At times, the
    delay between consecutive deliveries may not match the
    configuration. That is, delay can be more or less than configured
    backoff.

    Attributes:
        minimum_backoff (google.protobuf.duration_pb2.Duration):
            The minimum delay between consecutive
            deliveries of a given message. Value should be
            between 0 and 600 seconds. Defaults to 10
            seconds.
        maximum_backoff (google.protobuf.duration_pb2.Duration):
            The maximum delay between consecutive
            deliveries of a given message. Value should be
            between 0 and 600 seconds. Defaults to 600
            seconds.
    """

    minimum_backoff: duration_pb2.Duration = proto.Field(
        proto.MESSAGE,
        number=1,
        message=duration_pb2.Duration,
    )
    maximum_backoff: duration_pb2.Duration = proto.Field(
        proto.MESSAGE,
        number=2,
        message=duration_pb2.Duration,
    )


class DeadLetterPolicy(proto.Message):
    r"""Dead lettering is done on a best effort basis. The same
    message might be dead lettered multiple times.

    If validation on any of the fields fails at subscription
    creation/updation, the create/update subscription request will
    fail.

    Attributes:
        dead_letter_topic (str):
            The name of the topic to which dead letter messages should
            be published. Format is
            ``projects/{project}/topics/{topic}``.The Cloud Pub/Sub
            service account associated with the enclosing subscription's
            parent project (i.e.,
            service-{project_number}@gcp-sa-pubsub.iam.gserviceaccount.com)
            must have permission to Publish() to this topic.

            The operation will fail if the topic does not exist. Users
            should ensure that there is a subscription attached to this
            topic since messages published to a topic with no
            subscriptions are lost.
        max_delivery_attempts (int):
            The maximum number of delivery attempts for any message. The
            value must be between 5 and 100.

            The number of delivery attempts is defined as 1 + (the sum
            of number of NACKs and number of times the acknowledgement
            deadline has been exceeded for the message).

            A NACK is any call to ModifyAckDeadline with a 0 deadline.
            Note that client libraries may automatically extend
            ack_deadlines.

            This field will be honored on a best effort basis.

            If this parameter is 0, a default value of 5 is used.
    """

    dead_letter_topic: str = proto.Field(
        proto.STRING,
        number=1,
    )
    max_delivery_attempts: int = proto.Field(
        proto.INT32,
        number=2,
    )


class ExpirationPolicy(proto.Message):
    r"""A policy that specifies the conditions for resource
    expiration (i.e., automatic resource deletion).

    Attributes:
        ttl (google.protobuf.duration_pb2.Duration):
            Specifies the "time-to-live" duration for an associated
            resource. The resource expires if it is not active for a
            period of ``ttl``. The definition of "activity" depends on
            the type of the associated resource. The minimum and maximum
            allowed values for ``ttl`` depend on the type of the
            associated resource, as well. If ``ttl`` is not set, the
            associated resource never expires.
    """

    ttl: duration_pb2.Duration = proto.Field(
        proto.MESSAGE,
        number=1,
        message=duration_pb2.Duration,
    )


class PushConfig(proto.Message):
    r"""Configuration for a push delivery endpoint.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        push_endpoint (str):
            A URL locating the endpoint to which messages should be
            pushed. For example, a Webhook endpoint might use
            ``https://example.com/push``.
        attributes (MutableMapping[str, str]):
            Endpoint configuration attributes that can be used to
            control different aspects of the message delivery.

            The only currently supported attribute is
            ``x-goog-version``, which you can use to change the format
            of the pushed message. This attribute indicates the version
            of the data expected by the endpoint. This controls the
            shape of the pushed message (i.e., its fields and metadata).

            If not present during the ``CreateSubscription`` call, it
            will default to the version of the Pub/Sub API used to make
            such call. If not present in a ``ModifyPushConfig`` call,
            its value will not be changed. ``GetSubscription`` calls
            will always return a valid version, even if the subscription
            was created without this attribute.

            The only supported values for the ``x-goog-version``
            attribute are:

            -  ``v1beta1``: uses the push format defined in the v1beta1
               Pub/Sub API.
            -  ``v1`` or ``v1beta2``: uses the push format defined in
               the v1 Pub/Sub API.

            For example: ``attributes { "x-goog-version": "v1" }``
        oidc_token (google.pubsub_v1.types.PushConfig.OidcToken):
            If specified, Pub/Sub will generate and attach an OIDC JWT
            token as an ``Authorization`` header in the HTTP request for
            every pushed message.

            This field is a member of `oneof`_ ``authentication_method``.
        pubsub_wrapper (google.pubsub_v1.types.PushConfig.PubsubWrapper):
            When set, the payload to the push endpoint is
            in the form of the JSON representation of a
            PubsubMessage
            (https://cloud.google.com/pubsub/docs/reference/rpc/google.pubsub.v1#pubsubmessage).

            This field is a member of `oneof`_ ``wrapper``.
        no_wrapper (google.pubsub_v1.types.PushConfig.NoWrapper):
            When set, the payload to the push endpoint is
            not wrapped.

            This field is a member of `oneof`_ ``wrapper``.
    """

    class OidcToken(proto.Message):
        r"""Contains information needed for generating an `OpenID Connect
        token <https://developers.google.com/identity/protocols/OpenIDConnect>`__.

        Attributes:
            service_account_email (str):
                `Service account
                email <https://cloud.google.com/iam/docs/service-accounts>`__
                used for generating the OIDC token. For more information on
                setting up authentication, see `Push
                subscriptions <https://cloud.google.com/pubsub/docs/push>`__.
            audience (str):
                Audience to be used when generating OIDC
                token. The audience claim identifies the
                recipients that the JWT is intended for. The
                audience value is a single case-sensitive
                string. Having multiple values (array) for the
                audience field is not supported. More info about
                the OIDC JWT token audience here:
                https://tools.ietf.org/html/rfc7519#section-4.1.3
                Note: if not specified, the Push endpoint URL
                will be used.
        """

        service_account_email: str = proto.Field(
            proto.STRING,
            number=1,
        )
        audience: str = proto.Field(
            proto.STRING,
            number=2,
        )

    class PubsubWrapper(proto.Message):
        r"""The payload to the push endpoint is in the form of the JSON
        representation of a PubsubMessage
        (https://cloud.google.com/pubsub/docs/reference/rpc/google.pubsub.v1#pubsubmessage).

        """

    class NoWrapper(proto.Message):
        r"""Sets the ``data`` field as the HTTP body for delivery.

        Attributes:
            write_metadata (bool):
                When true, writes the Pub/Sub message metadata to
                ``x-goog-pubsub-<KEY>:<VAL>`` headers of the HTTP request.
                Writes the Pub/Sub message attributes to ``<KEY>:<VAL>``
                headers of the HTTP request.
        """

        write_metadata: bool = proto.Field(
            proto.BOOL,
            number=1,
        )

    push_endpoint: str = proto.Field(
        proto.STRING,
        number=1,
    )
    attributes: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=2,
    )
    oidc_token: OidcToken = proto.Field(
        proto.MESSAGE,
        number=3,
        oneof="authentication_method",
        message=OidcToken,
    )
    pubsub_wrapper: PubsubWrapper = proto.Field(
        proto.MESSAGE,
        number=4,
        oneof="wrapper",
        message=PubsubWrapper,
    )
    no_wrapper: NoWrapper = proto.Field(
        proto.MESSAGE,
        number=5,
        oneof="wrapper",
        message=NoWrapper,
    )


class BigQueryConfig(proto.Message):
    r"""Configuration for a BigQuery subscription.

    Attributes:
        table (str):
            The name of the table to which to write data,
            of the form {projectId}.{datasetId}.{tableId}
        use_topic_schema (bool):
            When true, use the topic's schema as the
            columns to write to in BigQuery, if it exists.
        write_metadata (bool):
            When true, write the subscription name, message_id,
            publish_time, attributes, and ordering_key to additional
            columns in the table. The subscription name, message_id, and
            publish_time fields are put in their own columns while all
            other message properties (other than data) are written to a
            JSON object in the attributes column.
        drop_unknown_fields (bool):
            When true and use_topic_schema is true, any fields that are
            a part of the topic schema that are not part of the BigQuery
            table schema are dropped when writing to BigQuery.
            Otherwise, the schemas must be kept in sync and any messages
            with extra fields are not written and remain in the
            subscription's backlog.
        state (google.pubsub_v1.types.BigQueryConfig.State):
            Output only. An output-only field that
            indicates whether or not the subscription can
            receive messages.
    """

    class State(proto.Enum):
        r"""Possible states for a BigQuery subscription.

        Values:
            STATE_UNSPECIFIED (0):
                Default value. This value is unused.
            ACTIVE (1):
                The subscription can actively send messages
                to BigQuery
            PERMISSION_DENIED (2):
                Cannot write to the BigQuery table because of permission
                denied errors. This can happen if

                -  Pub/Sub SA has not been granted the `appropriate BigQuery
                   IAM
                   permissions <https://cloud.google.com/pubsub/docs/create-subscription#assign_bigquery_service_account>`__
                -  bigquery.googleapis.com API is not enabled for the
                   project
                   (`instructions <https://cloud.google.com/service-usage/docs/enable-disable>`__)
            NOT_FOUND (3):
                Cannot write to the BigQuery table because it
                does not exist.
            SCHEMA_MISMATCH (4):
                Cannot write to the BigQuery table due to a
                schema mismatch.
        """
        STATE_UNSPECIFIED = 0
        ACTIVE = 1
        PERMISSION_DENIED = 2
        NOT_FOUND = 3
        SCHEMA_MISMATCH = 4

    table: str = proto.Field(
        proto.STRING,
        number=1,
    )
    use_topic_schema: bool = proto.Field(
        proto.BOOL,
        number=2,
    )
    write_metadata: bool = proto.Field(
        proto.BOOL,
        number=3,
    )
    drop_unknown_fields: bool = proto.Field(
        proto.BOOL,
        number=4,
    )
    state: State = proto.Field(
        proto.ENUM,
        number=5,
        enum=State,
    )


class CloudStorageConfig(proto.Message):
    r"""Configuration for a Cloud Storage subscription.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        bucket (str):
            Required. User-provided name for the Cloud Storage bucket.
            The bucket must be created by the user. The bucket name must
            be without any prefix like "gs://". See the [bucket naming
            requirements]
            (https://cloud.google.com/storage/docs/buckets#naming).
        filename_prefix (str):
            User-provided prefix for Cloud Storage filename. See the
            `object naming
            requirements <https://cloud.google.com/storage/docs/objects#naming>`__.
        filename_suffix (str):
            User-provided suffix for Cloud Storage filename. See the
            `object naming
            requirements <https://cloud.google.com/storage/docs/objects#naming>`__.
            Must not end in "/".
        text_config (google.pubsub_v1.types.CloudStorageConfig.TextConfig):
            If set, message data will be written to Cloud
            Storage in text format.

            This field is a member of `oneof`_ ``output_format``.
        avro_config (google.pubsub_v1.types.CloudStorageConfig.AvroConfig):
            If set, message data will be written to Cloud
            Storage in Avro format.

            This field is a member of `oneof`_ ``output_format``.
        max_duration (google.protobuf.duration_pb2.Duration):
            The maximum duration that can elapse before a
            new Cloud Storage file is created. Min 1 minute,
            max 10 minutes, default 5 minutes. May not
            exceed the subscription's acknowledgement
            deadline.
        max_bytes (int):
            The maximum bytes that can be written to a Cloud Storage
            file before a new file is created. Min 1 KB, max 10 GiB. The
            max_bytes limit may be exceeded in cases where messages are
            larger than the limit.
        state (google.pubsub_v1.types.CloudStorageConfig.State):
            Output only. An output-only field that
            indicates whether or not the subscription can
            receive messages.
    """

    class State(proto.Enum):
        r"""Possible states for a Cloud Storage subscription.

        Values:
            STATE_UNSPECIFIED (0):
                Default value. This value is unused.
            ACTIVE (1):
                The subscription can actively send messages
                to Cloud Storage.
            PERMISSION_DENIED (2):
                Cannot write to the Cloud Storage bucket
                because of permission denied errors.
            NOT_FOUND (3):
                Cannot write to the Cloud Storage bucket
                because it does not exist.
        """
        STATE_UNSPECIFIED = 0
        ACTIVE = 1
        PERMISSION_DENIED = 2
        NOT_FOUND = 3

    class TextConfig(proto.Message):
        r"""Configuration for writing message data in text format.
        Message payloads will be written to files as raw text, separated
        by a newline.

        """

    class AvroConfig(proto.Message):
        r"""Configuration for writing message data in Avro format.
        Message payloads and metadata will be written to files as an
        Avro binary.

        Attributes:
            write_metadata (bool):
                When true, write the subscription name, message_id,
                publish_time, attributes, and ordering_key as additional
                fields in the output. The subscription name, message_id, and
                publish_time fields are put in their own fields while all
                other message properties other than data (for example, an
                ordering_key, if present) are added as entries in the
                attributes map.
        """

        write_metadata: bool = proto.Field(
            proto.BOOL,
            number=1,
        )

    bucket: str = proto.Field(
        proto.STRING,
        number=1,
    )
    filename_prefix: str = proto.Field(
        proto.STRING,
        number=2,
    )
    filename_suffix: str = proto.Field(
        proto.STRING,
        number=3,
    )
    text_config: TextConfig = proto.Field(
        proto.MESSAGE,
        number=4,
        oneof="output_format",
        message=TextConfig,
    )
    avro_config: AvroConfig = proto.Field(
        proto.MESSAGE,
        number=5,
        oneof="output_format",
        message=AvroConfig,
    )
    max_duration: duration_pb2.Duration = proto.Field(
        proto.MESSAGE,
        number=6,
        message=duration_pb2.Duration,
    )
    max_bytes: int = proto.Field(
        proto.INT64,
        number=7,
    )
    state: State = proto.Field(
        proto.ENUM,
        number=9,
        enum=State,
    )


class ReceivedMessage(proto.Message):
    r"""A message and its corresponding acknowledgment ID.

    Attributes:
        ack_id (str):
            This ID can be used to acknowledge the
            received message.
        message (google.pubsub_v1.types.PubsubMessage):
            The message.
        delivery_attempt (int):
            The approximate number of times that Cloud Pub/Sub has
            attempted to deliver the associated message to a subscriber.

            More precisely, this is 1 + (number of NACKs) + (number of
            ack_deadline exceeds) for this message.

            A NACK is any call to ModifyAckDeadline with a 0 deadline.
            An ack_deadline exceeds event is whenever a message is not
            acknowledged within ack_deadline. Note that ack_deadline is
            initially Subscription.ackDeadlineSeconds, but may get
            extended automatically by the client library.

            Upon the first delivery of a given message,
            ``delivery_attempt`` will have a value of 1. The value is
            calculated at best effort and is approximate.

            If a DeadLetterPolicy is not set on the subscription, this
            will be 0.
    """

    ack_id: str = proto.Field(
        proto.STRING,
        number=1,
    )
    message: "PubsubMessage" = proto.Field(
        proto.MESSAGE,
        number=2,
        message="PubsubMessage",
    )
    delivery_attempt: int = proto.Field(
        proto.INT32,
        number=3,
    )


class GetSubscriptionRequest(proto.Message):
    r"""Request for the GetSubscription method.

    Attributes:
        subscription (str):
            Required. The name of the subscription to get. Format is
            ``projects/{project}/subscriptions/{sub}``.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )


class UpdateSubscriptionRequest(proto.Message):
    r"""Request for the UpdateSubscription method.

    Attributes:
        subscription (google.pubsub_v1.types.Subscription):
            Required. The updated subscription object.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. Indicates which fields in the
            provided subscription to update. Must be
            specified and non-empty.
    """

    subscription: "Subscription" = proto.Field(
        proto.MESSAGE,
        number=1,
        message="Subscription",
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=2,
        message=field_mask_pb2.FieldMask,
    )


class ListSubscriptionsRequest(proto.Message):
    r"""Request for the ``ListSubscriptions`` method.

    Attributes:
        project (str):
            Required. The name of the project in which to list
            subscriptions. Format is ``projects/{project-id}``.
        page_size (int):
            Maximum number of subscriptions to return.
        page_token (str):
            The value returned by the last
            ``ListSubscriptionsResponse``; indicates that this is a
            continuation of a prior ``ListSubscriptions`` call, and that
            the system should return the next page of data.
    """

    project: str = proto.Field(
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
    r"""Response for the ``ListSubscriptions`` method.

    Attributes:
        subscriptions (MutableSequence[google.pubsub_v1.types.Subscription]):
            The subscriptions that match the request.
        next_page_token (str):
            If not empty, indicates that there may be more subscriptions
            that match the request; this value should be passed in a new
            ``ListSubscriptionsRequest`` to get more subscriptions.
    """

    @property
    def raw_page(self):
        return self

    subscriptions: MutableSequence["Subscription"] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message="Subscription",
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class DeleteSubscriptionRequest(proto.Message):
    r"""Request for the DeleteSubscription method.

    Attributes:
        subscription (str):
            Required. The subscription to delete. Format is
            ``projects/{project}/subscriptions/{sub}``.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ModifyPushConfigRequest(proto.Message):
    r"""Request for the ModifyPushConfig method.

    Attributes:
        subscription (str):
            Required. The name of the subscription. Format is
            ``projects/{project}/subscriptions/{sub}``.
        push_config (google.pubsub_v1.types.PushConfig):
            Required. The push configuration for future deliveries.

            An empty ``pushConfig`` indicates that the Pub/Sub system
            should stop pushing messages from the given subscription and
            allow messages to be pulled and acknowledged - effectively
            pausing the subscription if ``Pull`` or ``StreamingPull`` is
            not called.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )
    push_config: "PushConfig" = proto.Field(
        proto.MESSAGE,
        number=2,
        message="PushConfig",
    )


class PullRequest(proto.Message):
    r"""Request for the ``Pull`` method.

    Attributes:
        subscription (str):
            Required. The subscription from which messages should be
            pulled. Format is
            ``projects/{project}/subscriptions/{sub}``.
        return_immediately (bool):
            Optional. If this field set to true, the system will respond
            immediately even if it there are no messages available to
            return in the ``Pull`` response. Otherwise, the system may
            wait (for a bounded amount of time) until at least one
            message is available, rather than returning no messages.
            Warning: setting this field to ``true`` is discouraged
            because it adversely impacts the performance of ``Pull``
            operations. We recommend that users do not set this field.
        max_messages (int):
            Required. The maximum number of messages to
            return for this request. Must be a positive
            integer. The Pub/Sub system may return fewer
            than the number specified.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )
    return_immediately: bool = proto.Field(
        proto.BOOL,
        number=2,
    )
    max_messages: int = proto.Field(
        proto.INT32,
        number=3,
    )


class PullResponse(proto.Message):
    r"""Response for the ``Pull`` method.

    Attributes:
        received_messages (MutableSequence[google.pubsub_v1.types.ReceivedMessage]):
            Received Pub/Sub messages. The list will be empty if there
            are no more messages available in the backlog, or if no
            messages could be returned before the request timeout. For
            JSON, the response can be entirely empty. The Pub/Sub system
            may return fewer than the ``maxMessages`` requested even if
            there are more messages available in the backlog.
    """

    received_messages: MutableSequence["ReceivedMessage"] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message="ReceivedMessage",
    )


class ModifyAckDeadlineRequest(proto.Message):
    r"""Request for the ModifyAckDeadline method.

    Attributes:
        subscription (str):
            Required. The name of the subscription. Format is
            ``projects/{project}/subscriptions/{sub}``.
        ack_ids (MutableSequence[str]):
            Required. List of acknowledgment IDs.
        ack_deadline_seconds (int):
            Required. The new ack deadline with respect to the time this
            request was sent to the Pub/Sub system. For example, if the
            value is 10, the new ack deadline will expire 10 seconds
            after the ``ModifyAckDeadline`` call was made. Specifying
            zero might immediately make the message available for
            delivery to another subscriber client. This typically
            results in an increase in the rate of message redeliveries
            (that is, duplicates). The minimum deadline you can specify
            is 0 seconds. The maximum deadline you can specify is 600
            seconds (10 minutes).
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )
    ack_ids: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=4,
    )
    ack_deadline_seconds: int = proto.Field(
        proto.INT32,
        number=3,
    )


class AcknowledgeRequest(proto.Message):
    r"""Request for the Acknowledge method.

    Attributes:
        subscription (str):
            Required. The subscription whose message is being
            acknowledged. Format is
            ``projects/{project}/subscriptions/{sub}``.
        ack_ids (MutableSequence[str]):
            Required. The acknowledgment ID for the messages being
            acknowledged that was returned by the Pub/Sub system in the
            ``Pull`` response. Must not be empty.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )
    ack_ids: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=2,
    )


class StreamingPullRequest(proto.Message):
    r"""Request for the ``StreamingPull`` streaming RPC method. This request
    is used to establish the initial stream as well as to stream
    acknowledgements and ack deadline modifications from the client to
    the server.

    Attributes:
        subscription (str):
            Required. The subscription for which to initialize the new
            stream. This must be provided in the first request on the
            stream, and must not be set in subsequent requests from
            client to server. Format is
            ``projects/{project}/subscriptions/{sub}``.
        ack_ids (MutableSequence[str]):
            List of acknowledgement IDs for acknowledging previously
            received messages (received on this stream or a different
            stream). If an ack ID has expired, the corresponding message
            may be redelivered later. Acknowledging a message more than
            once will not result in an error. If the acknowledgement ID
            is malformed, the stream will be aborted with status
            ``INVALID_ARGUMENT``.
        modify_deadline_seconds (MutableSequence[int]):
            The list of new ack deadlines for the IDs listed in
            ``modify_deadline_ack_ids``. The size of this list must be
            the same as the size of ``modify_deadline_ack_ids``. If it
            differs the stream will be aborted with
            ``INVALID_ARGUMENT``. Each element in this list is applied
            to the element in the same position in
            ``modify_deadline_ack_ids``. The new ack deadline is with
            respect to the time this request was sent to the Pub/Sub
            system. Must be >= 0. For example, if the value is 10, the
            new ack deadline will expire 10 seconds after this request
            is received. If the value is 0, the message is immediately
            made available for another streaming or non-streaming pull
            request. If the value is < 0 (an error), the stream will be
            aborted with status ``INVALID_ARGUMENT``.
        modify_deadline_ack_ids (MutableSequence[str]):
            List of acknowledgement IDs whose deadline will be modified
            based on the corresponding element in
            ``modify_deadline_seconds``. This field can be used to
            indicate that more time is needed to process a message by
            the subscriber, or to make the message available for
            redelivery if the processing was interrupted.
        stream_ack_deadline_seconds (int):
            Required. The ack deadline to use for the
            stream. This must be provided in the first
            request on the stream, but it can also be
            updated on subsequent requests from client to
            server. The minimum deadline you can specify is
            10 seconds. The maximum deadline you can specify
            is 600 seconds (10 minutes).
        client_id (str):
            A unique identifier that is used to distinguish client
            instances from each other. Only needs to be provided on the
            initial request. When a stream disconnects and reconnects
            for the same stream, the client_id should be set to the same
            value so that state associated with the old stream can be
            transferred to the new stream. The same client_id should not
            be used for different client instances.
        max_outstanding_messages (int):
            Flow control settings for the maximum number of outstanding
            messages. When there are ``max_outstanding_messages`` or
            more currently sent to the streaming pull client that have
            not yet been acked or nacked, the server stops sending more
            messages. The sending of messages resumes once the number of
            outstanding messages is less than this value. If the value
            is <= 0, there is no limit to the number of outstanding
            messages. This property can only be set on the initial
            StreamingPullRequest. If it is set on a subsequent request,
            the stream will be aborted with status ``INVALID_ARGUMENT``.
        max_outstanding_bytes (int):
            Flow control settings for the maximum number of outstanding
            bytes. When there are ``max_outstanding_bytes`` or more
            worth of messages currently sent to the streaming pull
            client that have not yet been acked or nacked, the server
            will stop sending more messages. The sending of messages
            resumes once the number of outstanding bytes is less than
            this value. If the value is <= 0, there is no limit to the
            number of outstanding bytes. This property can only be set
            on the initial StreamingPullRequest. If it is set on a
            subsequent request, the stream will be aborted with status
            ``INVALID_ARGUMENT``.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )
    ack_ids: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=2,
    )
    modify_deadline_seconds: MutableSequence[int] = proto.RepeatedField(
        proto.INT32,
        number=3,
    )
    modify_deadline_ack_ids: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=4,
    )
    stream_ack_deadline_seconds: int = proto.Field(
        proto.INT32,
        number=5,
    )
    client_id: str = proto.Field(
        proto.STRING,
        number=6,
    )
    max_outstanding_messages: int = proto.Field(
        proto.INT64,
        number=7,
    )
    max_outstanding_bytes: int = proto.Field(
        proto.INT64,
        number=8,
    )


class StreamingPullResponse(proto.Message):
    r"""Response for the ``StreamingPull`` method. This response is used to
    stream messages from the server to the client.

    Attributes:
        received_messages (MutableSequence[google.pubsub_v1.types.ReceivedMessage]):
            Received Pub/Sub messages. This will not be
            empty.
        acknowledge_confirmation (google.pubsub_v1.types.StreamingPullResponse.AcknowledgeConfirmation):
            This field will only be set if
            ``enable_exactly_once_delivery`` is set to ``true``.
        modify_ack_deadline_confirmation (google.pubsub_v1.types.StreamingPullResponse.ModifyAckDeadlineConfirmation):
            This field will only be set if
            ``enable_exactly_once_delivery`` is set to ``true``.
        subscription_properties (google.pubsub_v1.types.StreamingPullResponse.SubscriptionProperties):
            Properties associated with this subscription.
    """

    class AcknowledgeConfirmation(proto.Message):
        r"""Acknowledgement IDs sent in one or more previous requests to
        acknowledge a previously received message.

        Attributes:
            ack_ids (MutableSequence[str]):
                Successfully processed acknowledgement IDs.
            invalid_ack_ids (MutableSequence[str]):
                List of acknowledgement IDs that were
                malformed or whose acknowledgement deadline has
                expired.
            unordered_ack_ids (MutableSequence[str]):
                List of acknowledgement IDs that were out of
                order.
            temporary_failed_ack_ids (MutableSequence[str]):
                List of acknowledgement IDs that failed
                processing with temporary issues.
        """

        ack_ids: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=1,
        )
        invalid_ack_ids: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=2,
        )
        unordered_ack_ids: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=3,
        )
        temporary_failed_ack_ids: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=4,
        )

    class ModifyAckDeadlineConfirmation(proto.Message):
        r"""Acknowledgement IDs sent in one or more previous requests to
        modify the deadline for a specific message.

        Attributes:
            ack_ids (MutableSequence[str]):
                Successfully processed acknowledgement IDs.
            invalid_ack_ids (MutableSequence[str]):
                List of acknowledgement IDs that were
                malformed or whose acknowledgement deadline has
                expired.
            temporary_failed_ack_ids (MutableSequence[str]):
                List of acknowledgement IDs that failed
                processing with temporary issues.
        """

        ack_ids: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=1,
        )
        invalid_ack_ids: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=2,
        )
        temporary_failed_ack_ids: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=3,
        )

    class SubscriptionProperties(proto.Message):
        r"""Subscription properties sent as part of the response.

        Attributes:
            exactly_once_delivery_enabled (bool):
                True iff exactly once delivery is enabled for
                this subscription.
            message_ordering_enabled (bool):
                True iff message ordering is enabled for this
                subscription.
        """

        exactly_once_delivery_enabled: bool = proto.Field(
            proto.BOOL,
            number=1,
        )
        message_ordering_enabled: bool = proto.Field(
            proto.BOOL,
            number=2,
        )

    received_messages: MutableSequence["ReceivedMessage"] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message="ReceivedMessage",
    )
    acknowledge_confirmation: AcknowledgeConfirmation = proto.Field(
        proto.MESSAGE,
        number=5,
        message=AcknowledgeConfirmation,
    )
    modify_ack_deadline_confirmation: ModifyAckDeadlineConfirmation = proto.Field(
        proto.MESSAGE,
        number=3,
        message=ModifyAckDeadlineConfirmation,
    )
    subscription_properties: SubscriptionProperties = proto.Field(
        proto.MESSAGE,
        number=4,
        message=SubscriptionProperties,
    )


class CreateSnapshotRequest(proto.Message):
    r"""Request for the ``CreateSnapshot`` method.

    Attributes:
        name (str):
            Required. User-provided name for this snapshot. If the name
            is not provided in the request, the server will assign a
            random name for this snapshot on the same project as the
            subscription. Note that for REST API requests, you must
            specify a name. See the `resource name
            rules <https://cloud.google.com/pubsub/docs/admin#resource_names>`__.
            Format is ``projects/{project}/snapshots/{snap}``.
        subscription (str):
            Required. The subscription whose backlog the snapshot
            retains. Specifically, the created snapshot is guaranteed to
            retain: (a) The existing backlog on the subscription. More
            precisely, this is defined as the messages in the
            subscription's backlog that are unacknowledged upon the
            successful completion of the ``CreateSnapshot`` request; as
            well as: (b) Any messages published to the subscription's
            topic following the successful completion of the
            CreateSnapshot request. Format is
            ``projects/{project}/subscriptions/{sub}``.
        labels (MutableMapping[str, str]):
            See `Creating and managing
            labels <https://cloud.google.com/pubsub/docs/labels>`__.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    subscription: str = proto.Field(
        proto.STRING,
        number=2,
    )
    labels: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=3,
    )


class UpdateSnapshotRequest(proto.Message):
    r"""Request for the UpdateSnapshot method.

    Attributes:
        snapshot (google.pubsub_v1.types.Snapshot):
            Required. The updated snapshot object.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. Indicates which fields in the
            provided snapshot to update. Must be specified
            and non-empty.
    """

    snapshot: "Snapshot" = proto.Field(
        proto.MESSAGE,
        number=1,
        message="Snapshot",
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=2,
        message=field_mask_pb2.FieldMask,
    )


class Snapshot(proto.Message):
    r"""A snapshot resource. Snapshots are used in
    `Seek <https://cloud.google.com/pubsub/docs/replay-overview>`__
    operations, which allow you to manage message acknowledgments in
    bulk. That is, you can set the acknowledgment state of messages in
    an existing subscription to the state captured by a snapshot.

    Attributes:
        name (str):
            The name of the snapshot.
        topic (str):
            The name of the topic from which this
            snapshot is retaining messages.
        expire_time (google.protobuf.timestamp_pb2.Timestamp):
            The snapshot is guaranteed to exist up until this time. A
            newly-created snapshot expires no later than 7 days from the
            time of its creation. Its exact lifetime is determined at
            creation by the existing backlog in the source subscription.
            Specifically, the lifetime of the snapshot is
            ``7 days - (age of oldest unacked message in the subscription)``.
            For example, consider a subscription whose oldest unacked
            message is 3 days old. If a snapshot is created from this
            subscription, the snapshot -- which will always capture this
            3-day-old backlog as long as the snapshot exists -- will
            expire in 4 days. The service will refuse to create a
            snapshot that would expire in less than 1 hour after
            creation.
        labels (MutableMapping[str, str]):
            See [Creating and managing labels]
            (https://cloud.google.com/pubsub/docs/labels).
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    topic: str = proto.Field(
        proto.STRING,
        number=2,
    )
    expire_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=3,
        message=timestamp_pb2.Timestamp,
    )
    labels: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=4,
    )


class GetSnapshotRequest(proto.Message):
    r"""Request for the GetSnapshot method.

    Attributes:
        snapshot (str):
            Required. The name of the snapshot to get. Format is
            ``projects/{project}/snapshots/{snap}``.
    """

    snapshot: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListSnapshotsRequest(proto.Message):
    r"""Request for the ``ListSnapshots`` method.

    Attributes:
        project (str):
            Required. The name of the project in which to list
            snapshots. Format is ``projects/{project-id}``.
        page_size (int):
            Maximum number of snapshots to return.
        page_token (str):
            The value returned by the last ``ListSnapshotsResponse``;
            indicates that this is a continuation of a prior
            ``ListSnapshots`` call, and that the system should return
            the next page of data.
    """

    project: str = proto.Field(
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


class ListSnapshotsResponse(proto.Message):
    r"""Response for the ``ListSnapshots`` method.

    Attributes:
        snapshots (MutableSequence[google.pubsub_v1.types.Snapshot]):
            The resulting snapshots.
        next_page_token (str):
            If not empty, indicates that there may be more snapshot that
            match the request; this value should be passed in a new
            ``ListSnapshotsRequest``.
    """

    @property
    def raw_page(self):
        return self

    snapshots: MutableSequence["Snapshot"] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message="Snapshot",
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class DeleteSnapshotRequest(proto.Message):
    r"""Request for the ``DeleteSnapshot`` method.

    Attributes:
        snapshot (str):
            Required. The name of the snapshot to delete. Format is
            ``projects/{project}/snapshots/{snap}``.
    """

    snapshot: str = proto.Field(
        proto.STRING,
        number=1,
    )


class SeekRequest(proto.Message):
    r"""Request for the ``Seek`` method.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        subscription (str):
            Required. The subscription to affect.
        time (google.protobuf.timestamp_pb2.Timestamp):
            The time to seek to. Messages retained in the subscription
            that were published before this time are marked as
            acknowledged, and messages retained in the subscription that
            were published after this time are marked as unacknowledged.
            Note that this operation affects only those messages
            retained in the subscription (configured by the combination
            of ``message_retention_duration`` and
            ``retain_acked_messages``). For example, if ``time``
            corresponds to a point before the message retention window
            (or to a point before the system's notion of the
            subscription creation time), only retained messages will be
            marked as unacknowledged, and already-expunged messages will
            not be restored.

            This field is a member of `oneof`_ ``target``.
        snapshot (str):
            The snapshot to seek to. The snapshot's topic must be the
            same as that of the provided subscription. Format is
            ``projects/{project}/snapshots/{snap}``.

            This field is a member of `oneof`_ ``target``.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )
    time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof="target",
        message=timestamp_pb2.Timestamp,
    )
    snapshot: str = proto.Field(
        proto.STRING,
        number=3,
        oneof="target",
    )


class SeekResponse(proto.Message):
    r"""Response for the ``Seek`` method (this response is empty)."""


__all__ = tuple(sorted(__protobuf__.manifest))
