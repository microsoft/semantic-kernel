# Copyright 2017, Google LLC All rights reserved.
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

from __future__ import absolute_import

import abc
import enum
import typing
from typing import Optional, Sequence


if typing.TYPE_CHECKING:  # pragma: NO COVER
    from google.cloud import pubsub_v1
    from google.cloud.pubsub_v1 import types
    from google.pubsub_v1 import types as gapic_types


class Batch(metaclass=abc.ABCMeta):
    """The base batching class for Pub/Sub publishing.

    Although the :class:`~.pubsub_v1.publisher.batch.thread.Batch` class, based
    on :class:`threading.Thread`, is fine for most cases, advanced
    users may need to implement something based on a different concurrency
    model.

    This class defines the interface for the Batch implementation;
    subclasses may be passed as the ``batch_class`` argument to
    :class:`~.pubsub_v1.client.PublisherClient`.

    The batching behavior works like this: When the
    :class:`~.pubsub_v1.publisher.client.Client` is asked to publish a new
    message, it requires a batch. The client will see if there is an
    already-opened batch for the given topic; if there is, then the message
    is sent to that batch. If there is not, then a new batch is created
    and the message put there.

    When a new batch is created, it automatically starts a timer counting
    down to the maximum latency before the batch should commit.
    Essentially, if enough time passes, the batch automatically commits
    regardless of how much is in it. However, if either the message count or
    size thresholds are encountered first, then the batch will commit early.
    """

    def __len__(self):
        """Return the number of messages currently in the batch."""
        return len(self.messages)

    @staticmethod
    @abc.abstractmethod
    def make_lock():  # pragma: NO COVER
        """Return a lock in the chosen concurrency model.

        Returns:
            ContextManager: A newly created lock.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def messages(self) -> Sequence["gapic_types.PubsubMessage"]:  # pragma: NO COVER
        """Return the messages currently in the batch.

        Returns:
            The messages currently in the batch.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def size(self) -> int:  # pragma: NO COVER
        """Return the total size of all of the messages currently in the batch.

        The size includes any overhead of the actual ``PublishRequest`` that is
        sent to the backend.

        Returns:
            int: The total size of all of the messages currently
                 in the batch (including the request overhead), in bytes.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def settings(self) -> "types.BatchSettings":  # pragma: NO COVER
        """Return the batch settings.

        Returns:
            The batch settings. These are considered immutable once the batch has
            been opened.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def status(self) -> "BatchStatus":  # pragma: NO COVER
        """Return the status of this batch.

        Returns:
            The status of this batch. All statuses are human-readable, all-lowercase
            strings. The ones represented in the :class:`BaseBatch.Status` enum are
            special, but other statuses are permitted.
        """
        raise NotImplementedError

    def cancel(
        self, cancellation_reason: "BatchCancellationReason"
    ) -> None:  # pragma: NO COVER
        """Complete pending futures with an exception.

        This method must be called before publishing starts (ie: while the
        batch is still accepting messages.)

        Args:
            cancellation_reason:
                The reason why this batch has been cancelled.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def publish(
        self, message: "gapic_types.PubsubMessage"
    ) -> Optional["pubsub_v1.publisher.futures.Future"]:  # pragma: NO COVER
        """Publish a single message.

        Add the given message to this object; this will cause it to be
        published once the batch either has enough messages or a sufficient
        period of time has elapsed.

        This method is called by :meth:`~.PublisherClient.publish`.

        Args:
            message: The Pub/Sub message.

        Returns:
            An object conforming to the :class:`concurrent.futures.Future` interface.
            If :data:`None` is returned, that signals that the batch cannot
            accept a message.
        """
        raise NotImplementedError


class BatchStatus(str, enum.Enum):
    """An enum-like class representing valid statuses for a batch."""

    ACCEPTING_MESSAGES = "accepting messages"
    STARTING = "starting"
    IN_PROGRESS = "in progress"
    ERROR = "error"
    SUCCESS = "success"


class BatchCancellationReason(str, enum.Enum):
    """An enum-like class representing reasons why a batch was cancelled."""

    PRIOR_ORDERED_MESSAGE_FAILED = (
        "Batch cancelled because prior ordered message for the same key has "
        "failed. This batch has been cancelled to avoid out-of-order publish."
    )
    CLIENT_STOPPED = "Batch cancelled because the publisher client has been stopped."
