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

import logging
import threading
import time
import typing
from typing import Any, Callable, List, Optional, Sequence

import google.api_core.exceptions
from google.api_core import gapic_v1
from google.cloud.pubsub_v1.publisher import exceptions
from google.cloud.pubsub_v1.publisher import futures
from google.cloud.pubsub_v1.publisher._batch import base
from google.pubsub_v1 import types as gapic_types

if typing.TYPE_CHECKING:  # pragma: NO COVER
    from google.cloud import pubsub_v1
    from google.cloud.pubsub_v1 import types
    from google.cloud.pubsub_v1.publisher import Client as PublisherClient
    from google.pubsub_v1.services.publisher.client import OptionalRetry

_LOGGER = logging.getLogger(__name__)
_CAN_COMMIT = (base.BatchStatus.ACCEPTING_MESSAGES, base.BatchStatus.STARTING)
_SERVER_PUBLISH_MAX_BYTES = 10 * 1000 * 1000  # max accepted size of PublishRequest

_raw_proto_pubbsub_message = gapic_types.PubsubMessage.pb()


class Batch(base.Batch):
    """A batch of messages.

    The batch is the internal group of messages which are either awaiting
    publication or currently in progress.

    A batch is automatically created by the PublisherClient when the first
    message to be published is received; subsequent messages are added to
    that batch until the process of actual publishing _starts_.

    Once this occurs, any new messages sent to :meth:`publish` open a new
    batch.

    If you are using this library, you most likely do not need to instantiate
    batch objects directly; they will be created for you. If you want to
    change the actual batching settings, see the ``batching`` argument on
    :class:`~.pubsub_v1.PublisherClient`.

    Any properties or methods on this class which are not defined in
    :class:`~.pubsub_v1.publisher.batch.BaseBatch` should be considered
    implementation details.

    Args:
        client:
            The publisher client used to create this batch.
        topic:
            The topic. The format for this is ``projects/{project}/topics/{topic}``.
        settings:
            The settings for batch publishing. These should be considered immutable
            once the batch has been opened.
        batch_done_callback:
            Callback called when the response for a batch publish has been received.
            Called with one boolean argument: successfully published or a permanent
            error occurred. Temporary errors are not surfaced because they are retried
            at a lower level.
        commit_when_full:
            Whether to commit the batch when the batch is full.
        commit_retry:
            Designation of what errors, if any, should be retried when commiting
            the batch. If not provided, a default retry is used.
        commit_timeout:
            The timeout to apply when commiting the batch. If not provided, a default
            timeout is used.
    """

    def __init__(
        self,
        client: "PublisherClient",
        topic: str,
        settings: "types.BatchSettings",
        batch_done_callback: Callable[[bool], Any] = None,
        commit_when_full: bool = True,
        commit_retry: "OptionalRetry" = gapic_v1.method.DEFAULT,
        commit_timeout: "types.OptionalTimeout" = gapic_v1.method.DEFAULT,
    ):
        self._client = client
        self._topic = topic
        self._settings = settings
        self._batch_done_callback = batch_done_callback
        self._commit_when_full = commit_when_full

        self._state_lock = threading.Lock()
        # These members are all communicated between threads; ensure that
        # any writes to them use the "state lock" to remain atomic.
        # _futures list should remain unchanged after batch
        # status changed from ACCEPTING_MESSAGES to any other
        # in order to avoid race conditions
        self._futures: List[futures.Future] = []
        self._messages: List[gapic_types.PubsubMessage] = []
        self._status = base.BatchStatus.ACCEPTING_MESSAGES

        # The initial size is not zero, we need to account for the size overhead
        # of the PublishRequest message itself.
        self._base_request_size = gapic_types.PublishRequest(topic=topic)._pb.ByteSize()
        self._size = self._base_request_size

        self._commit_retry = commit_retry
        self._commit_timeout = commit_timeout

    @staticmethod
    def make_lock() -> threading.Lock:
        """Return a threading lock.

        Returns:
            A newly created lock.
        """
        return threading.Lock()

    @property
    def client(self) -> "PublisherClient":
        """A publisher client."""
        return self._client

    @property
    def messages(self) -> Sequence[gapic_types.PubsubMessage]:
        """The messages currently in the batch."""
        return self._messages

    @property
    def settings(self) -> "types.BatchSettings":
        """Return the batch settings.

        Returns:
            The batch settings. These are considered immutable once the batch has
            been opened.
        """
        return self._settings

    @property
    def size(self) -> int:
        """Return the total size of all of the messages currently in the batch.

        The size includes any overhead of the actual ``PublishRequest`` that is
        sent to the backend.

        Returns:
            The total size of all of the messages currently in the batch (including
            the request overhead), in bytes.
        """
        return self._size

    @property
    def status(self) -> base.BatchStatus:
        """Return the status of this batch.

        Returns:
            The status of this batch. All statuses are human-readable, all-lowercase
            strings.
        """
        return self._status

    def cancel(self, cancellation_reason: base.BatchCancellationReason) -> None:
        """Complete pending futures with an exception.

        This method must be called before publishing starts (ie: while the
        batch is still accepting messages.)

        Args:
            The reason why this batch has been cancelled.
        """

        with self._state_lock:
            assert (
                self._status == base.BatchStatus.ACCEPTING_MESSAGES
            ), "Cancel should not be called after sending has started."

            exc = RuntimeError(cancellation_reason.value)
            for future in self._futures:
                future.set_exception(exc)
            self._status = base.BatchStatus.ERROR

    def commit(self) -> None:
        """Actually publish all of the messages on the active batch.

        .. note::

            This method is non-blocking. It opens a new thread, which calls
            :meth:`_commit`, which does block.

        This synchronously sets the batch status to "starting", and then opens
        a new thread, which handles actually sending the messages to Pub/Sub.

        If the current batch is **not** accepting messages, this method
        does nothing.
        """

        # Set the status to "starting" synchronously, to ensure that
        # this batch will necessarily not accept new messages.
        with self._state_lock:
            if self._status == base.BatchStatus.ACCEPTING_MESSAGES:
                self._status = base.BatchStatus.STARTING
            else:
                return

        self._start_commit_thread()

    def _start_commit_thread(self) -> None:
        """Start a new thread to actually handle the commit."""
        # NOTE: If the thread is *not* a daemon, a memory leak exists due to a CPython issue.
        # https://github.com/googleapis/python-pubsub/issues/395#issuecomment-829910303
        # https://github.com/googleapis/python-pubsub/issues/395#issuecomment-830092418
        commit_thread = threading.Thread(
            name="Thread-CommitBatchPublisher", target=self._commit, daemon=True
        )
        commit_thread.start()

    def _commit(self) -> None:
        """Actually publish all of the messages on the active batch.

        This moves the batch out from being the active batch to an in progress
        batch on the publisher, and then the batch is discarded upon
        completion.

        .. note::

            This method blocks. The :meth:`commit` method is the non-blocking
            version, which calls this one.
        """
        with self._state_lock:
            if self._status in _CAN_COMMIT:
                self._status = base.BatchStatus.IN_PROGRESS
            else:
                # If, in the intervening period between when this method was
                # called and now, the batch started to be committed, or
                # completed a commit, then no-op at this point.
                _LOGGER.debug(
                    "Batch is already in progress or has been cancelled, "
                    "exiting commit"
                )
                return

        # Once in the IN_PROGRESS state, no other thread can publish additional
        # messages or initiate a commit (those operations become a no-op), thus
        # it is safe to release the state lock here. Releasing the lock avoids
        # blocking other threads in case api.publish() below takes a long time
        # to complete.
        # https://github.com/googleapis/google-cloud-python/issues/8036

        # Sanity check: If there are no messages, no-op.
        if not self._messages:
            _LOGGER.debug("No messages to publish, exiting commit")
            self._status = base.BatchStatus.SUCCESS
            return

        # Begin the request to publish these messages.
        # Log how long the underlying request takes.
        start = time.time()

        batch_transport_succeeded = True
        try:
            # Performs retries for errors defined by the retry configuration.
            response = self._client._gapic_publish(
                topic=self._topic,
                messages=self._messages,
                retry=self._commit_retry,
                timeout=self._commit_timeout,
            )
        except google.api_core.exceptions.GoogleAPIError as exc:
            # We failed to publish, even after retries, so set the exception on
            # all futures and exit.
            self._status = base.BatchStatus.ERROR

            for future in self._futures:
                future.set_exception(exc)

            batch_transport_succeeded = False
            if self._batch_done_callback is not None:
                # Failed to publish batch.
                self._batch_done_callback(batch_transport_succeeded)

            _LOGGER.exception("Failed to publish %s messages.", len(self._futures))
            return

        end = time.time()
        _LOGGER.debug("gRPC Publish took %s seconds.", end - start)

        if len(response.message_ids) == len(self._futures):
            # Iterate over the futures on the queue and return the response
            # IDs. We are trusting that there is a 1:1 mapping, and raise
            # an exception if not.
            self._status = base.BatchStatus.SUCCESS
            for message_id, future in zip(response.message_ids, self._futures):
                future.set_result(message_id)
        else:
            # Sanity check: If the number of message IDs is not equal to
            # the number of futures I have, then something went wrong.
            self._status = base.BatchStatus.ERROR
            exception = exceptions.PublishError(
                "Some messages were not successfully published."
            )

            for future in self._futures:
                future.set_exception(exception)

            # Unknown error -> batch failed to be correctly transported/
            batch_transport_succeeded = False

            _LOGGER.error(
                "Only %s of %s messages were published.",
                len(response.message_ids),
                len(self._futures),
            )

        if self._batch_done_callback is not None:
            self._batch_done_callback(batch_transport_succeeded)

    def publish(
        self, message: gapic_types.PubsubMessage
    ) -> Optional["pubsub_v1.publisher.futures.Future"]:
        """Publish a single message.

        Add the given message to this object; this will cause it to be
        published once the batch either has enough messages or a sufficient
        period of time has elapsed. If the batch is full or the commit is
        already in progress, the method does not do anything.

        This method is called by :meth:`~.PublisherClient.publish`.

        Args:
            message: The Pub/Sub message.

        Returns:
            An object conforming to the :class:`~concurrent.futures.Future` interface
            or :data:`None`. If :data:`None` is returned, that signals that the batch
            cannot accept a message.

        Raises:
            pubsub_v1.publisher.exceptions.MessageTooLargeError: If publishing
                the ``message`` would exceed the max size limit on the backend.
        """

        # Coerce the type, just in case.
        if not isinstance(message, gapic_types.PubsubMessage):
            # For performance reasons, the message should be constructed by directly
            # using the raw protobuf class, and only then wrapping it into the
            # higher-level PubsubMessage class.
            vanilla_pb = _raw_proto_pubbsub_message(**message)
            message = gapic_types.PubsubMessage.wrap(vanilla_pb)

        future = None

        with self._state_lock:
            assert (
                self._status != base.BatchStatus.ERROR
            ), "Publish after stop() or publish error."

            if self.status != base.BatchStatus.ACCEPTING_MESSAGES:
                return None

            size_increase = gapic_types.PublishRequest(
                messages=[message]
            )._pb.ByteSize()

            if (self._base_request_size + size_increase) > _SERVER_PUBLISH_MAX_BYTES:
                err_msg = (
                    "The message being published would produce too large a publish "
                    "request that would exceed the maximum allowed size on the "
                    "backend ({} bytes).".format(_SERVER_PUBLISH_MAX_BYTES)
                )
                raise exceptions.MessageTooLargeError(err_msg)

            new_size = self._size + size_increase
            new_count = len(self._messages) + 1

            size_limit = min(self.settings.max_bytes, _SERVER_PUBLISH_MAX_BYTES)
            overflow = new_size > size_limit or new_count >= self.settings.max_messages

            if not self._messages or not overflow:

                # Store the actual message in the batch's message queue.
                self._messages.append(message)
                self._size = new_size

                # Track the future on this batch (so that the result of the
                # future can be set).
                future = futures.Future()
                self._futures.append(future)

        # Try to commit, but it must be **without** the lock held, since
        # ``commit()`` will try to obtain the lock.
        if self._commit_when_full and overflow:
            self.commit()

        return future

    def _set_status(self, status: base.BatchStatus):
        self._status = status
