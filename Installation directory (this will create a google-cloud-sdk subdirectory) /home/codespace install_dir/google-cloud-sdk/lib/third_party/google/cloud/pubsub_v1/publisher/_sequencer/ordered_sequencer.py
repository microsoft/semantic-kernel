# Copyright 2019, Google LLC All rights reserved.
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

import enum
import collections
import threading
import typing
from typing import Deque, Iterable, Sequence

from google.api_core import gapic_v1
from google.cloud.pubsub_v1.publisher import futures
from google.cloud.pubsub_v1.publisher import exceptions
from google.cloud.pubsub_v1.publisher._sequencer import base as sequencer_base
from google.cloud.pubsub_v1.publisher._batch import base as batch_base
from google.pubsub_v1 import types as gapic_types

if typing.TYPE_CHECKING:  # pragma: NO COVER
    from google.cloud.pubsub_v1 import types
    from google.cloud.pubsub_v1.publisher import _batch
    from google.cloud.pubsub_v1.publisher.client import Client as PublisherClient
    from google.pubsub_v1.services.publisher.client import OptionalRetry


class _OrderedSequencerStatus(str, enum.Enum):
    """An enum-like class representing valid statuses for an OrderedSequencer.

    Starting state: ACCEPTING_MESSAGES
    Valid transitions:
      ACCEPTING_MESSAGES -> PAUSED (on permanent error)
      ACCEPTING_MESSAGES -> STOPPED  (when user calls stop() explicitly)
      ACCEPTING_MESSAGES -> FINISHED  (all batch publishes finish normally)

      PAUSED -> ACCEPTING_MESSAGES  (when user unpauses)
      PAUSED -> STOPPED  (when user calls stop() explicitly)

      STOPPED -> FINISHED (user stops client and the one remaining batch finishes
                           publish)
      STOPPED -> PAUSED (stop() commits one batch, which fails permanently)

      FINISHED -> ACCEPTING_MESSAGES (publish happens while waiting for cleanup)
      FINISHED -> STOPPED (when user calls stop() explicitly)
    Illegal transitions:
      PAUSED -> FINISHED (since all batches are cancelled on pause, there should
                          not be any that finish normally. paused sequencers
                          should not be cleaned up because their presence
                          indicates that the ordering key needs to be resumed)
      STOPPED -> ACCEPTING_MESSAGES (no way to make a user-stopped sequencer
                                     accept messages again. this is okay since
                                     stop() should only be called on shutdown.)
      FINISHED -> PAUSED (no messages remain in flight, so they can't cause a
                          permanent error and pause the sequencer)
    """

    # Accepting publishes and/or waiting for result of batch publish
    ACCEPTING_MESSAGES = "accepting messages"
    # Permanent error occurred. User must unpause this sequencer to resume
    # publishing. This is done to maintain ordering.
    PAUSED = "paused"
    # No more publishes allowed. There may be an outstanding batch that will
    # call the _batch_done_callback when it's done (success or error.)
    STOPPED = "stopped"
    # No more work to do. Waiting to be cleaned-up. A publish will transform
    # this sequencer back into the normal accepting-messages state.
    FINISHED = "finished"


class OrderedSequencer(sequencer_base.Sequencer):
    """Sequences messages into batches ordered by an ordering key for one topic.

    A sequencer always has at least one batch in it, unless paused or stopped.
    When no batches remain, the |publishes_done_callback| is called so the
    client can perform cleanup.

    Public methods are thread-safe.

    Args:
        client:
            The publisher client used to create this sequencer.
        topic:
            The topic. The format for this is ``projects/{project}/topics/{topic}``.
        ordering_key:
            The ordering key for this sequencer.
    """

    def __init__(self, client: "PublisherClient", topic: str, ordering_key: str):
        self._client = client
        self._topic = topic
        self._ordering_key = ordering_key
        # Guards the variables below
        self._state_lock = threading.Lock()
        # Batches ordered from first (head/left) to last (right/tail).
        # Invariant: always has at least one batch after the first publish,
        # unless paused or stopped.
        self._ordered_batches: Deque["_batch.thread.Batch"] = collections.deque()
        # See _OrderedSequencerStatus for valid state transitions.
        self._state = _OrderedSequencerStatus.ACCEPTING_MESSAGES

    def is_finished(self) -> bool:
        """Whether the sequencer is finished and should be cleaned up.

        Returns:
            Whether the sequencer is finished and should be cleaned up.
        """
        with self._state_lock:
            return self._state == _OrderedSequencerStatus.FINISHED

    def stop(self) -> None:
        """Permanently stop this sequencer.

        This differs from pausing, which may be resumed. Immediately commits
        the first batch and cancels the rest.

        Raises:
            RuntimeError:
                If called after stop() has already been called.
        """
        with self._state_lock:
            if self._state == _OrderedSequencerStatus.STOPPED:
                raise RuntimeError("Ordered sequencer already stopped.")

            self._state = _OrderedSequencerStatus.STOPPED
            if self._ordered_batches:
                # Give only the first batch the chance to finish.
                self._ordered_batches[0].commit()

                # Cancel the rest of the batches and remove them from the deque
                # of batches.
                while len(self._ordered_batches) > 1:
                    # Pops from the tail until it leaves only the head in the
                    # deque.
                    batch = self._ordered_batches.pop()
                    batch.cancel(batch_base.BatchCancellationReason.CLIENT_STOPPED)

    def commit(self) -> None:
        """Commit the first batch, if unpaused.

        If paused or no batches exist, this method does nothing.

        Raises:
            RuntimeError:
                If called after stop() has already been called.
        """
        with self._state_lock:
            if self._state == _OrderedSequencerStatus.STOPPED:
                raise RuntimeError("Ordered sequencer already stopped.")

            if self._state != _OrderedSequencerStatus.PAUSED and self._ordered_batches:
                # It's okay to commit the same batch more than once. The
                # operation is idempotent.
                self._ordered_batches[0].commit()

    def _batch_done_callback(self, success: bool) -> None:
        """Deal with completion of a batch.

        Called when a batch has finished publishing, with either a success
        or a failure. (Temporary failures are retried infinitely when
        ordering keys are enabled.)
        """
        ensure_cleanup_and_commit_timer_runs = False
        with self._state_lock:
            assert self._state != _OrderedSequencerStatus.PAUSED, (
                "This method should not be called after pause() because "
                "pause() should have cancelled all of the batches."
            )
            assert self._state != _OrderedSequencerStatus.FINISHED, (
                "This method should not be called after all batches have been "
                "finished."
            )

            # Message futures for the batch have been completed (either with a
            # result or an exception) already, so remove the batch.
            self._ordered_batches.popleft()

            if success:
                if len(self._ordered_batches) == 0:
                    # Mark this sequencer as finished.
                    # If new messages come in for this ordering key and this
                    # sequencer hasn't been cleaned up yet, it will go back
                    # into accepting-messages state. Otherwise, the client
                    # must create a new OrderedSequencer.
                    self._state = _OrderedSequencerStatus.FINISHED
                    # Ensure cleanup thread runs at some point.
                    ensure_cleanup_and_commit_timer_runs = True
                elif len(self._ordered_batches) == 1:
                    # Wait for messages and/or commit timeout
                    # Ensure there's actually a commit timer thread that'll commit
                    # after a delay.
                    ensure_cleanup_and_commit_timer_runs = True
                else:
                    # If there is more than one batch, we know that the next batch
                    # must be full and, therefore, ready to be committed.
                    self._ordered_batches[0].commit()
            else:
                # Unrecoverable error detected
                self._pause()

        if ensure_cleanup_and_commit_timer_runs:
            self._client.ensure_cleanup_and_commit_timer_runs()

    def _pause(self) -> None:
        """Pause this sequencer: set state to paused, cancel all batches, and
        clear the list of ordered batches.

        _state_lock must be taken before calling this method.
        """
        assert (
            self._state != _OrderedSequencerStatus.FINISHED
        ), "Pause should not be called after all batches have finished."
        self._state = _OrderedSequencerStatus.PAUSED
        for batch in self._ordered_batches:
            batch.cancel(
                batch_base.BatchCancellationReason.PRIOR_ORDERED_MESSAGE_FAILED
            )
        self._ordered_batches.clear()

    def unpause(self) -> None:
        """Unpause this sequencer.

        Raises:
            RuntimeError:
                If called when the ordering key has not been paused.
        """
        with self._state_lock:
            if self._state != _OrderedSequencerStatus.PAUSED:
                raise RuntimeError("Ordering key is not paused.")
            self._state = _OrderedSequencerStatus.ACCEPTING_MESSAGES

    def _create_batch(
        self,
        commit_retry: "OptionalRetry" = gapic_v1.method.DEFAULT,
        commit_timeout: "types.OptionalTimeout" = gapic_v1.method.DEFAULT,
    ) -> "_batch.thread.Batch":
        """Create a new batch using the client's batch class and other stored
            settings.

        Args:
            commit_retry:
                The retry settings to apply when publishing the batch.
            commit_timeout:
                The timeout to apply when publishing the batch.
        """
        return self._client._batch_class(
            client=self._client,
            topic=self._topic,
            settings=self._client.batch_settings,
            batch_done_callback=self._batch_done_callback,
            commit_when_full=False,
            commit_retry=commit_retry,
            commit_timeout=commit_timeout,
        )

    def publish(
        self,
        message: gapic_types.PubsubMessage,
        retry: "OptionalRetry" = gapic_v1.method.DEFAULT,
        timeout: "types.OptionalTimeout" = gapic_v1.method.DEFAULT,
    ) -> futures.Future:
        """Publish message for this ordering key.

        Args:
            message:
                The Pub/Sub message.
            retry:
                The retry settings to apply when publishing the message.
            timeout:
                The timeout to apply when publishing the message.

        Returns:
            A class instance that conforms to Python Standard library's
            :class:`~concurrent.futures.Future` interface (but not an
            instance of that class). The future might return immediately with a
            PublishToPausedOrderingKeyException if the ordering key is paused.
            Otherwise, the future tracks the lifetime of the message publish.

        Raises:
            RuntimeError:
                If called after this sequencer has been stopped, either by
                a call to stop() or after all batches have been published.
        """
        with self._state_lock:
            if self._state == _OrderedSequencerStatus.PAUSED:
                errored_future = futures.Future()
                exception = exceptions.PublishToPausedOrderingKeyException(
                    self._ordering_key
                )
                errored_future.set_exception(exception)
                return errored_future

            # If waiting to be cleaned-up, convert to accepting messages to
            # prevent this sequencer from being cleaned-up only to have another
            # one with the same ordering key created immediately afterward.
            if self._state == _OrderedSequencerStatus.FINISHED:
                self._state = _OrderedSequencerStatus.ACCEPTING_MESSAGES

            if self._state == _OrderedSequencerStatus.STOPPED:
                raise RuntimeError("Cannot publish on a stopped sequencer.")

            assert (
                self._state == _OrderedSequencerStatus.ACCEPTING_MESSAGES
            ), "Publish is only allowed in accepting-messages state."

            if not self._ordered_batches:
                new_batch = self._create_batch(
                    commit_retry=retry, commit_timeout=timeout
                )
                self._ordered_batches.append(new_batch)

            batch = self._ordered_batches[-1]
            future = batch.publish(message)
            while future is None:
                batch = self._create_batch(commit_retry=retry, commit_timeout=timeout)
                self._ordered_batches.append(batch)
                future = batch.publish(message)

            return future

    # Used only for testing.
    def _set_batch(self, batch: "_batch.thread.Batch") -> None:
        self._ordered_batches = collections.deque([batch])

    # Used only for testing.
    def _set_batches(self, batches: Iterable["_batch.thread.Batch"]) -> None:
        self._ordered_batches = collections.deque(batches)

    # Used only for testing.
    def _get_batches(self) -> Sequence["_batch.thread.Batch"]:
        return self._ordered_batches
